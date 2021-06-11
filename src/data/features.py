import pandas as pd
import numpy as np


def order_request_value(df_members, df_products):
    '''
    calculate the order value for each order_request
    and add order_request_value to df_members.

    Parameters
    ----------
    df_members : pd.DataFrame
    df_products : pd.DataFrame

    Returns
    -------
    df_members : pd.DataFrame
        members dataframe with added order_request_value column
    '''
    # add new column with nan values
    df_members['order_request_value'] = np.nan

    # loop through df_members to get 'order_ID' and 'order_requests'
    for i in df_members.index:
        order_ID = df_members.order_ID[i]
        order_request = df_members.order_requests[i]  # iPython needs eval() to recognize dict

        # get 'product_ID' and 'filled_amount' from order_request
        order_request_df = pd.DataFrame(order_request, index=['filled', 'ordered']).T.reset_index()
        product_ID = order_request_df['index']
        filled_amount = order_request_df['filled'].replace(',', '.', regex=True)
        filled_amount = filled_amount.replace(r'^\s*$', 0, regex=True).astype('float')

        # access net_price from df_products and calculate order_request_value
        net_price = df_products.loc[(order_ID, product_ID), 'net_price'].reset_index(drop=True)
        order_request_value = np.sum(net_price * filled_amount).round(2)

        # assign order_request_value to df_members
        df_members.loc[i, 'order_request_value'] = order_request_value

    return df_members


def main(df_orders, df_members, df_products):
    '''
    This function adds following features to the dataframes:
    - df_orders: 'total_order_value', 'num_participating_members'
    - df_products: 'net_total_price'
    - df_members: 'order_request_value', 'delivery_date'

    Parameters
    ----------
    df_members : pd.DataFrame
    df_products : pd.DataFrame
    df_products : pd.DataFrame

    Returns
    -------
    df_orders, df_members, df_products : pd.DataFrame
    '''
    # create column 'net_total_price' (net_price * amount_ordered) for each product
    df_products['net_total_price'] = df_products.net_price * df_products.amount_ordered

    # merges delivery_date to df_members dataframe
    df_members = df_members.reset_index()
    df_members = df_members.merge(df_orders['delivery_date'].reset_index(),  # reset_index since order_ID is in index
                                  how='left',
                                  on='order_ID')

    # reassign df_name to df_members after merge
    df_members.df_name = 'members'
    df_members._metadata += ['df_name']

    # calculate total_order_value and add to df_orders
    total_order_value = df_products.groupby('order_ID')['net_total_price'].sum()
    df_orders['total_order_value'] = total_order_value.round(2)

    # get num_participating_members and add to df_orders
    df_orders['num_participating_members'] = df_members.groupby('order_ID').size()

    # get order_request_value and add to members dataframe
    df_members = order_request_value(df_members, df_products)

    return df_orders, df_members, df_products
