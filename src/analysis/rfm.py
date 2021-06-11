import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ..data import utils
sns.set()


def main(df_members, freq='W', export_csv=True, export_plot=True):
    '''
    [summary]

    Parameters
    ----------
    df_members : pd.DataFrame
        scoop members dataframe
    freq : {'W', 'M'}, optional
        Set frequency interval, by default 'W'
    export_csv : bool, optional
        Exports RFM Table as .csv to ./data/processed, by default True
    export_plot : bool, optional
        Exports plot to ./figures, by default True

    Returns
    -------
    rfm_table : pd.DataFrame

    Usage
    -----
    rfm_table = src.rfm.main(df_members, freq='W', export_csv=True, export_plot=True)
    '''
    # check if freq input is valid
    if freq not in ['W', 'M']:
        print("Your input is not valid! Choose either {'W', 'M'} as freq.")
        return

    # create rfm table
    rfm_table = make_table(df_members, freq)
    # add rfm score
    rfm_table, bin_info = add_score(rfm_table, freq)

    # export rfm table as csv to processed
    if export_csv:
        utils.export_as_csv([rfm_table])
        print('export rfm_table done')

    if export_plot:
        plot(rfm_table, df_members, bin_info, freq)

    return rfm_table


def make_table(df_members, freq):
    '''
    A function to create a rfm table from a transactions dataframe,
    by calculating recency (time period since last delivery),
    frequency (count of active periods) and
    monetary_value (avg. monetary_value per period).

    Parameters
    ----------
    df_members : pd.DataFrame
        scoop members dataframe
    freq : {'W', 'M'}
        Set frequency interval

    Returns
    -------
    pd.DataFrame
        RFM Table
    '''
    # select columns of interest
    cols_of_interest = ['member_ID', 'delivery_date', 'order_request_value']
    df = df_members[cols_of_interest].copy()

    # removing supercoop company account
    df = df.loc[df.member_ID != 46]

    # create rfm table
    period_end = df.delivery_date.max()  # TODO

    # set delivery_date as index to convert into PeriodIndex of 'W'
    # then cast back to DatetimeIndex of timestamps, at beginning of period.
    rfm_table = df.set_index('delivery_date').to_period(
        freq).to_timestamp().reset_index()

    # sum all orders based on member_id and time (week)
    rfm_table = rfm_table.groupby(['delivery_date', 'member_ID'],
                                  sort=False, as_index=False).sum()

    # get the most recent delivery_date, the frequencycount of deliverys and the mean order value
    rfm_table = rfm_table.groupby('member_ID').agg({'delivery_date': 'max', 'member_ID': 'count',
                                                    'order_request_value': 'mean'})
    # rename all columns
    rfm_table.rename(columns={'delivery_date': 'recency', 'member_ID': 'frequency',
                              'order_request_value': 'monetary_value'}, inplace=True)

    # calculating recency (with floor devision)
    freq_timedeltas = {'W': np.timedelta64(1, 'W'), 'M': np.timedelta64(1, 'M'),
                       'Q': np.timedelta64(3, 'M')}
    rfm_table['recency'] = (period_end -
                            rfm_table['recency']) // freq_timedeltas[freq]

    # set dataframe name
    rfm_table.df_name = 'rfm_table'
    rfm_table._metadata += ['df_name']

    return rfm_table


def add_score(rfm_table, freq):
    '''
    This Function calculates the RFM score using manually scaled bin ranges
    for recency (where low values score highest) and quartile bin ranges
    for frequency and monetary value.

    Parameters
    ----------
    rfm_table : pd.DataFrame
    freq : {'W', 'M'}
        Set frequency interval

    Returns
    -------
    rfm_table : pd.DataFrame
    bin_info : dict
        Bin ranges of R, F, M labels
    '''
    # recency score (small value is best)
    # scale recency bin range beased on freq
    r_range = [0, 0.25, 0.5, 1, np.inf]
    freqs = {'W': 52, 'M': 12, 'Q': 4}
    r_range = [x * freqs[freq] for x in r_range]

    # use pd.cut to create and label bins
    r_labels, r_bins = pd.cut(rfm_table.recency, bins=r_range, labels=[4, 3, 2, 1],
                              retbins=True, include_lowest=True)
    rfm_table['r_score'] = r_labels

    # frequency
    f_labels, f_bins = pd.qcut(rfm_table.frequency, 4,
                               retbins=True, labels=range(1, 5))
    rfm_table['f_score'] = f_labels

    # monetary value
    m_labels, m_bins = pd.qcut(rfm_table.monetary_value, 4,
                               retbins=True, labels=range(1, 5))
    rfm_table['m_score'] = m_labels

    # combined rfm score
    rfm_table['rfm_score'] = (rfm_table.r_score.astype(str) + rfm_table.f_score.astype(str)
                              + rfm_table.m_score.astype(str))

    # gather bin info for plotting
    bin_info = {'r': r_bins, 'f': f_bins, 'm': m_bins}

    return rfm_table, bin_info


def plot(rfm_table, df, bin_info, freq):
    '''
    Function to turn and export the RFM Table into a plot.

    Parameters
    ----------
    rfm_table : pd.DataFrame
    df : pd.DataFrame
        members dataframe
    bin_info : dict
        Bin ranges of R, F, M labels
    freq : {'W', 'M'}
        Set frequency interval
    '''
    # font and colors
    sns.set(rc={"axes.facecolor": "#ebebf1"})  # set grid color
    cmap = plt.cm.get_cmap('BuPu')
    dist_color = cmap(0.4)  # distributions color
    fontsizes = {'t1': 22, 't2': 18, 'labels': 14, 'annot': 14, 'foot': 10}

    # Figure and Gridspec
    # choose either constrained_layout or tight_layout
    fig = plt.figure(figsize=(18, 12), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=2/72, h_pad=4/72,
                                    wspace=1/72, hspace=1/72)

    gs_widths = [1, 1, 1]
    gs_heights = [1, 1, 1, 0.04]
    gs = fig.add_gridspec(4, 3, width_ratios=gs_widths,
                          height_ratios=gs_heights)

    # Axes
    ax1 = fig.add_subplot(gs[0:2, :])
    ax2 = fig.add_subplot(gs[2, 0])
    ax3 = fig.add_subplot(gs[2, 1], sharey=ax2)
    ax4 = fig.add_subplot(gs[2, 2], sharey=ax2)
    with sns.axes_style("white"):  # footnotes don't want a grid
        ax5 = fig.add_subplot(gs[-1, :])
        ax5.axis('off')

    # Heatmap (Ax1)
    # adding n and T labels
    n = len(rfm_table.index)
    t_min, t_max = pd.Period(df.delivery_date.min(), 'M'), pd.Period(
        df.delivery_date.max(), 'M')

    # dont use tight_layout since it pushes the cbar inside the axes. constrained_layout works fine.
    cbar_kws = {'label': 'Number of Members in Segment', 'fraction': 0.046,  # width of cbar
                "shrink": 1, 'extend': 'min', 'extendfrac': 0.05,
                "ticks": np.arange(0, 16), "drawedges": False}
    annot_kws = {'fontsize': fontsizes['annot']}

    heatmap_values, heatmap_labels = get_heatmap_labels(rfm_table)

    sns.heatmap(heatmap_values, ax=ax1, mask=heatmap_values.isnull(),
                annot=heatmap_labels, annot_kws=annot_kws,
                cmap=cmap, linewidths=2, fmt='s',
                cbar_kws=cbar_kws)

    ax1.set_title('Recency-Frequency Heatmap',
                  fontsize=fontsizes['t1'], fontweight='bold', loc='left')
    ax1.annotate(f"(t = {t_min.strftime('%b. %Y')} - {t_max.strftime('%b. %Y')}, n = {n})",
                 xy=(1, 1.0126), xycoords='axes fraction', ha='right')
    ax1.set_xlabel('Recency Score$^2$', fontsize=fontsizes['labels'])  # $$ wraps superscript
    ax1.set_ylabel('Frequency Score$^1$', fontsize=fontsizes['labels'])
    ax1.set_xticklabels(ax1.get_xticklabels())
    ax1.set_yticklabels(ax1.get_yticklabels(),
                        rotation=0)

    # Distribution plots (Ax2-Ax4)

    # Distribution bin ranges
    bins_recency = range(0, int(max(rfm_table['recency'])+4), 4)
    bins_frequency = range(0, int(max(rfm_table['frequency'])+4), 4)
    bins_monetary = range(0, int(max(rfm_table['monetary_value']))+5, 10)

    # Recency (Ax2)
    rfm_table.recency.plot.hist(bins=bins_recency, ax=ax2,
                                color=dist_color)
    ax2.set_title('Recency Distribution',
                  fontsize=fontsizes['t2'], fontweight='bold', loc='left')
    ax2.set_xlabel('Weeks since last order', fontsize=fontsizes['labels'])
    ax2.set_ylabel('Number of Members', fontsize=fontsizes['labels'])
    ax2.set_xticks(bins_recency)

    # Frequency (Ax3)
    rfm_table.frequency.plot.hist(bins=bins_frequency,
                                  ax=ax3,
                                  color=dist_color)
    ax3.set_title('Frequency Distribution',
                  fontsize=fontsizes['t2'], fontweight='bold', loc='left')
    ax3.set_xlabel('Weeks in which a member ordered',
                   fontsize=fontsizes['labels'])
    ax3.set_ylabel('Number of Members', fontsize=fontsizes['labels'])
    ax3.set_xticks(bins_frequency)

    # Monetary Value (Ax4)
    rfm_table.monetary_value.plot.hist(bins=bins_monetary,
                                       ax=ax4,
                                       color=dist_color)
    ax4.set_title('Monetary Value Distribution',
                  fontsize=fontsizes['t2'], fontweight='bold', loc='left')
    ax4.set_xlabel('avg. Spending in EUR', fontsize=fontsizes['labels'])
    ax4.set_ylabel('Number of Members', fontsize=fontsizes['labels'])
    ax4.set_xticks(bins_monetary)
    # quick fix for not showing outliers: TODO remove outliers in make_dataframe
    ax4.set_xlim(0, bins_monetary[-1]*0.95)

    # Footnotes (Ax5)
    freqstr = {'W': 'Weeks', 'M': 'Months'}
    r_annot = '$^2$ Recency Score Intervals in {5}    4: [{0:.0f} - {1:.0f}] > 3: ({1:.0f} - {2:.0f}] > 2: ({2:.0f} - {3:.0f}] > 1: ({3:.0f} - {4:.0f})'.format(*bin_info['r'], freqstr[freq])
    f_annot = '$^1$ Frequency Score Intervals   4: [{0:.1f} - {1:.1f}) > 3: [{1:.1f} - {2:.1f}) > 2: [{2:.1f} - {3:.1f}) > 1: [{3:.1f} - {4:.1f}]'.format(*np.flip(bin_info['f']))
    ax5.annotate(r_annot, xy=(0.36, 1), fontsize=fontsizes['foot'],
                 xycoords='axes fraction', textcoords='offset points',
                 va='center', ha='left', annotation_clip=False)
    ax5.annotate(f_annot, xy=(0., 1), fontsize=fontsizes['foot'],
                 xycoords='axes fraction', textcoords='offset points',
                 va='center', ha='left', annotation_clip=False)

    # save plot as png to .figures/
    figname = 'rfm_heatmap'
    utils.export_plot(fig, figname, freq)


def get_heatmap_labels(rfm_table):
    '''
    Takes in the rfm table and prepares the values and labels for the heatmap plot.

    Parameters
    ----------
    rfm_table : pd.DataFrame

    Returns
    -------
    heatmap_count : pd.DataFrame
        DataFrame of the member count in segment
    heatmap_labels : np.Array
        numpy array with identical shape as heatmap_count
    '''
    # create matrix of member counts
    heatmap_count = rfm_table.groupby(
        ['f_score', 'r_score']).m_score.count().unstack()
    heatmap_count.replace(0, np.nan, inplace=True)
    heatmap_count.sort_index(axis=0, ascending=False,
                             inplace=True)  # sort index
    heatmap_count.sort_index(axis=1, ascending=False,
                             inplace=True)  # sort columns

    # create matrix avg. monetary value
    heatmap_mv = rfm_table.groupby(
        ['f_score', 'r_score']).monetary_value.mean().unstack()
    heatmap_mv.sort_index(axis=0, ascending=False, inplace=True)  # sort index
    heatmap_mv.sort_index(axis=1, ascending=False,
                          inplace=True)  # sort columns

    # flatten and zip so labels can be used in for loop
    heatmap_labels = zip(heatmap_count.to_numpy().flatten(),
                         heatmap_mv.to_numpy().flatten())
    # wrap label values in stringform
    heatmap_labels = np.asarray(["{0:.0f} Members\n{1:.2f} EUR avg. Spending".format(
        count, mv) for count, mv in heatmap_labels])
    # reshape labels to fit heatmap count
    heatmap_labels = heatmap_labels.reshape(heatmap_count.shape)

    return heatmap_count, heatmap_labels
