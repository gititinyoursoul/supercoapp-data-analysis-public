import os
import pandas as pd


def export_as_csv(df_list):
    '''
    takes in a list of dataframes and an output directory path
    and exports the dataframes as csv-files to the chosen output directory.

    Parameters
    ----------
    df_list : List of pd.DataFrames
    '''
    # set abs export path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    RELATIV_EXPORT_PATH = '../../data/processed/'
    abs_export_path = os.path.join(script_dir, RELATIV_EXPORT_PATH)
    # timestamp of today as string
    todaystr = pd.to_datetime("today").strftime("%Y%m%d")

    for df in df_list:
        # get df_name
        df_name = df.df_name
        # create filename string
        filename = f'{todaystr}_scoop_{df_name}.csv'
        # export to .csv
        df.to_csv(abs_export_path + filename)
        print(f'{filename} exported to {abs_export_path}')


def export_plot(fig, figname, freq):
    '''
    Takes in a figure, name and frequency and saves the figure in ./figures

    Parameters
    ----------
    fig : plt.figure
    figname : str
    freq : str
        Frequency used in plot

    '''
    # filename
    todaystr = pd.to_datetime("today").strftime("%Y%m%d")
    if freq:
        filestr = f'_{freq}_{figname}.png'
    else:
        filestr = f'_{figname}.png'
    filename = todaystr + filestr

    # export path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    RELATIV_EXPORT_PATH = '../../figures/'
    abs_export_path = os.path.abspath(
        os.path.join(script_dir, RELATIV_EXPORT_PATH))

    # save file
    fig.savefig(abs_export_path + '/' + filename,
                dpi=300, bbox_inches='tight')
    print(f'{filename} exported to {abs_export_path}')


def load_data(folder_path='data/processed'):
    '''
    Load csv files and return the respective dataframes.

    Parameters
    ----------
    folder_path : str, optional
        relativ directory path to csv files, by default 'data/processed'

    Returns
    -------
    df_orders, df_members, df_products : pd.DataFrame
        Returns respective dataframes, None if not found

    Usage
    -----
    df_orders, df_members, df_products = src.load_data('data/processed')
    '''
    # return None if csv does not exist
    df_orders = df_members = df_products = None

    # list all files in folder_path
    listdir = os.listdir(folder_path)
    print(listdir)

    # read csv and create dataframes
    for csv in listdir:
        if 'orders' in csv:
            df_orders = pd.read_csv(folder_path + '/' + csv,
                                    index_col='order_ID',
                                    parse_dates=['delivery_date', 'created_at',
                                                 'updated_at'])
        elif 'members' in csv:
            df_members = pd.read_csv(folder_path + '/' + csv,
                                     index_col=[0],
                                     parse_dates=['delivery_date'])
            # reminder: scoop company account
            print('reminder: data from scoop company account (#46) is included')

        elif 'products' in csv:
            df_products = pd.read_csv(folder_path + '/' + csv,
                                      index_col=['order_ID', 'product_ID'])

    return df_orders, df_members, df_products
