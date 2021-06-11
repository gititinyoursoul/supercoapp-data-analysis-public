import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from operator import attrgetter
from ..data import utils
sns.set()


def main(df_members, freq='Q', export_plot=True):
    '''
    Main function to perform a cohort analysis.

    Args:
        df_members : pd.DataFrame
            [description]
        freq : {'Q', 'M'}, optional
            Set frequency interval of cohorts. Defaults to 'Q' (Quarter End Frequency).
        export_plot : bool, optional
            Exports plot of retention matrix to ./figures.

    Returns:
        retention_matrix : pd.DataFrame
        cohort_pivot : pd.DataFrame

    Usage:
        retention_matrix, cohort_pivot = src.cohort.main(df_members)
    '''
    # check if freq input is valid
    if freq not in ['M', 'Q']:
        print("Your input is not valid! Choose either {'M', 'Q'} as freq.")
        return

    # remove supercoop company account
    df_members = df_members.loc[df_members.member_ID != 46]

    retention_matrix, cohort_pivot = make_retention_matrix(df_members, freq)

    if export_plot:
        plot(retention_matrix, cohort_pivot, df_members, freq)

    return retention_matrix, cohort_pivot


def make_retention_matrix(df_members, freq):
    '''
    Create a retention matrix of df_members Dataframe.

    Parameters
    ----------
    df_members : pd.DataFrame
        scoop members dataframe
    freq : str or pd.DateOffset object
        Set the frequency interval of the matrix.

    Returns
    -------
    retention_matrix : pd.DataFrame
    cohort_pivot : pd.DataFrame

    Usage
    -----
    retention_matrix, cohort_pivot = src.cohort.make_retention_matrix(df_members)

    Recources
    ---------
    `introduction-to-cohort-analysis-in-python <https://towardsdatascience.com/a-step-by-step-introduction-to-cohort-analysis-in-python-a2cbbd8460ea>´
    '''
    # copy cols from dataframe
    cols = ['member_ID', 'delivery_date']
    members_cohort = df_members[cols].copy()

    # add column delivery_freq to dataframe
    members_cohort['delivery_freq'] = members_cohort['delivery_date'].dt.to_period(
        freq)

    # add cohort column (first_seen)
    members_cohort['cohort'] = members_cohort.groupby('member_ID')['delivery_date'] \
        .transform('min').dt.to_period(freq)
    members_cohort.reset_index(inplace=True, drop=True)

    # aggregate cohort
    members_cohort = members_cohort.groupby(['cohort', 'delivery_freq']) \
        .agg(n_members=('member_ID', 'nunique')) \
        .reset_index(drop=False)

    members_cohort['period_number'] = (members_cohort.delivery_freq
                                       - members_cohort.cohort).apply(attrgetter('n'))

    # create pivot table
    cohort_pivot = members_cohort.pivot_table(index='cohort',
                                              columns='period_number',
                                              values='n_members')

    # retention matrix
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.div(cohort_size, axis=0)

    return retention_matrix, cohort_pivot


def plot(retention_matrix, cohort_pivot, df_members, freq):
    '''
    Create a plot of a retention matrix and save image as a png in ./figures.

    Parameters
    ----------
    retention_matrix : pd.DataFrame
    cohort_pivot : pd.DataFrame
    df_members : pd.DataFrame
    freq : str
    '''
    cohort_size = cohort_pivot.iloc[:, 0]

    # colors and font
    cmap = plt.cm.get_cmap('BuPu')
    white_cmap = mcolors.ListedColormap(['white'])
    fontsizes = {'t1': 18, 'labels': 12, 'annot': 12}

    # set values for annotations
    n = sum(cohort_pivot.iloc[:, 0])
    t_min, t_max = pd.Period(df_members.delivery_date.min(), 'M'), pd.Period(
        df_members.delivery_date.max(), 'M')

    with sns.axes_style("white"):
        fig, ax = plt.subplots(1, 2, figsize=(12, 6), sharey=True,
                               gridspec_kw={'width_ratios': [1, 11]})

        # cohort size
        cohort_size_df = pd.DataFrame(cohort_size).rename(
            columns={0: 'cohort\n size'})
        sns.heatmap(cohort_size_df,
                    annot=True,
                    cbar=False,
                    fmt='g',
                    cmap=white_cmap,
                    ax=ax[0])
        ax[0].set_title('User Retention by Cohorts',
                        fontsize=fontsizes['t1'], fontweight='bold', loc='left')
        ax[1].annotate("(t = {0} - {1}, n = {2:.0f})".format(*[t_min.strftime('%b. %Y'),
                                                               t_max.strftime('%b. %Y'), n]),
                       xy=(0.42, 1.0215), xycoords='axes fraction')
        ax[0].set(ylabel='Cohorts')
        ax[0].tick_params(labelsize=fontsizes['labels'], labelrotation=0)

        # retention matrix
        sns.heatmap(retention_matrix,
                    mask=retention_matrix.isnull(),
                    annot=True,
                    cbar=True,
                    linewidths=0.005,
                    fmt='.0%',
                    cmap=cmap,
                    ax=ax[1])
        ax[1].set(xlabel='Number of periods', ylabel='')
        ax[1].tick_params(labelsize=fontsizes['labels'])

        # export plot as png to ./figures
        figname = 'retention_matrix'
        utils.export_plot(fig, figname, freq)
