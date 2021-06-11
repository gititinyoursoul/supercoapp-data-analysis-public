import pandas as pd
import numpy as np
from . import utils, features


def make_df_orders(path_dataclip):
    '''
    Takes in a json dump of the supercoop app
    and returns a processed dataframe of all orders.

    Parameters
    ----------
    path_dataclip : str
        file path to json dump from supercoop app

    Returns
    -------
    df_orders : pd.DataFrame
        processed orders dataframe
    '''
    # read JSON
    df_orders = pd.read_json(path_dataclip)
    # set df_name
    df_orders.df_name = 'orders'
    df_orders._metadata += ['df_name']

    # set column names
    df_orders.columns = ['order_ID', 'supplier_ID', 'positions_hash', 'delivery_date', 'created_at',
                         'updated_at', 'open_order', 'scoop_margin', 'supplier_margin']

    # set column 'order_ID' as index and drop old index
    df_orders.set_index('order_ID', drop=True, inplace=True)
    df_orders.sort_index(inplace=True)

    # parse dates to datetime ##
    date_cols = ['delivery_date', 'created_at', 'updated_at']
    # pd.to_datetime works only on strings/series not on DataFrames
    # df.stack() produces a pd.Series where all rows are stacked on top of each other,
    # then apllies pd.to_datetime(), therafter unstack() reverts everything to its original form.
    df_orders[date_cols] = pd.to_datetime(df_orders[date_cols].stack(), format='%Y-%m-%d').unstack()

    # Create 'members' and 'products' cols from 'position_hash' #
    # create new column with member values out of df_orders['positions_hash']
    df_orders['members'] = [df_orders.loc[i, 'positions_hash']['members'] for i in df_orders.index]
    # create new column with products values out of df_orders['positions_hash']
    df_orders['products'] = [df_orders.loc[i, 'positions_hash']['products'] for i in df_orders.index]
    # drop df_orders['positions_hash']
    df_orders = df_orders.drop('positions_hash', axis=1)

    return df_orders


def make_df_members(df_orders):
    '''
    Takes in the dataframe of scoop orders (df_orders),
    processes the data in the members column
    and returns the member data as a dataframe.

    Parameters
    ----------
    df_orders : pd.DataFrame
        dataframe with scoop orders

    Returns
    -------
    df_members : pd.DataFrame
        dataframe with scoop members
    '''
    # create empty DataFrame and insert an aditional column for order_ID
    df_members = pd.DataFrame()
    df_members.insert(0, 'order_ID', '')

    # loop through df_orders.index (i = Order_ID )
    for i in df_orders.index:
        order = pd.DataFrame(df_orders.members[i]).T
        order['order_ID'] = i
        df_members = pd.concat([df_members, order])

    # reset index
    df_members.index.name = 'member_ID'
    df_members.index = df_members.index.astype('int')

    # set dtypes
    df_members = df_members.astype({'collected?': 'bool'})

    # set df_name
    df_members.df_name = 'members'
    df_members._metadata += ['df_name']

    return df_members


def make_df_products(df_orders):
    '''
    Takes in a dataframe of scoop orders (df_orders),
    processes the data in the products column
    and returns the product data as a dataframe.

    Parameters
    ----------
    df_orders : pd.DataFrame
        dataframe with scoop orders

    Returns
    -------
    df_members : pd.DataFrame
        dataframe with scoop products
    '''
    # Create DataFrame of products dict in df_orders #

    # concat all positions of all orders into one dataframe
    df_products = pd.DataFrame()
    # insert new column 'Order_ID' at column position '0'
    df_products.insert(0, 'order_ID', '')

    for row in df_orders.index:
        order = pd.DataFrame(df_orders.products[row]).T
        order['order_ID'] = row
        df_products = pd.concat([df_products, order])

    # multi index #
    df_products.index.name = 'product_ID'  # set index name
    df_products.set_index('order_ID', append=True, inplace=True)  # append colum order_ID as second index
    df_products = df_products.reorder_levels(['order_ID', 'product_ID'], axis=0)  # reorder mulitindex

    # dtypes and string processing #
    # column names with float values
    float_cols = ['tax_rate', 'net_price', 'bundle_size', 'supplier_code', 'amount_ordered', 'bundles_ordered']
    # string replace
    df_products[float_cols] = df_products[float_cols].replace(',', '.', regex=True)
    df_products[float_cols] = df_products[float_cols].replace('', np.nan, regex=True)
    # change dtypes to float
    df_products = df_products.astype({'tax_rate': 'float', 'net_price': 'float', 'bundle_size': 'float',
                                      'amount_ordered': 'float', 'bundles_ordered': 'float'})

    # set df_name
    df_products.df_name = 'products'
    df_products._metadata += ['df_name']

    return df_products


def make_dataframes(raw_data_path, export_csv=True):
    '''
    Main Function to make all dataframes from json dump.

    Parameters
    ----------
    raw_data_path : str
        raw_data path of the scoop json dump
    export_csv : bool, optional
        Export processed dataframes as csv files to ./data/processed, by default True

    Returns
    -------
    df_orders, df_members, df_products : pd.DataFrame

    Usage
    -----
    df_orders, df_members, df_products = src.make_dataframes(raw_data_path)
    '''
    # initialize DataFrames
    df_orders = make_df_orders(raw_data_path)
    df_members = make_df_members(df_orders)
    df_products = make_df_products(df_orders)

    # drop 'members', 'products' columns
    df_orders.drop(['members', 'products'], axis=1, inplace=True)
    print('initialize dataframes done')

    # create all features
    df_orders, df_members, df_products = features.main(df_orders, df_members, df_products)
    print('create_all_features done')

    # export dataframes to ../data/processed
    if export_csv:
        utils.export_as_csv([df_orders, df_members, df_products])
        print('export dataframes done')

    return df_orders, df_members, df_products
