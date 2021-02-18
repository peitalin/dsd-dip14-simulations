import numpy as np
import pandas as pd
# plots
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplfinance as fplt

from src.curve_amm import Curve, get_y, stableswap_y, stableswap_x
from src.uniswap_amm import Uniswap, uniswap_y, uniswap_x, linear_y
from src.tax_functions import quadratic_tax, linear_tax, no_tax
from src.random import generate_trade


##### Testing/Debugging
from src.curve_amm import Curve, _xp, stableswap_y, stableswap_x, get_y, get_D
# c = Curve(100000, 500000, A=20)
# stableswap_x( 100000 + 1, [100000, 100000], 2000)
# (100001-100000)/(99999.04761917747 - 100000)

# 0.9895494479
# 0.9894878188482094
# 0.9898556552223209

c1 = Curve(100000, 100000, A=20)
c = Curve(100000, 100000, A=20)
c.swap(({ 'type': "sell", "amount": 10000 }), tax_function=no_tax)
c.swap(({ 'type': "buy", "amount": 10000 }), tax_function=no_tax)



avg_prices = dict({
    "quadratic_tax_uni": [],
    "linear_tax": [],
    "no_tax": [],
    "no_tax_curve": [],
    "slippage_tax_uni": [],
    "slippage_tax_curve": [],
    "quadratic_tax_curve": [],
})
avg_burns = dict({
    "quadratic_tax_uni": [],
    "linear_tax": [],
    "no_tax": [],
    "no_tax_curve": [],
    "slippage_tax_uni": [],
    "slippage_tax_curve": [],
    "quadratic_tax_curve": [],
})
avg_treasury_balances = dict({
    "quadratic_tax_uni": [],
    "linear_tax": [],
    "no_tax": [],
    "no_tax_curve": [],
    "slippage_tax_uni": [],
    "slippage_tax_curve": [],
    "quadratic_tax_curve": [],
})


if __name__=="__main__":
    print("DSD DIP-14 Curve AMM Simulations!")




mu = -2000
sigma = 10000
nobs = 8000
plot_variate = 'prices'
# plot_variate = 'treasury_balances'
# plot_variate = 'burns'

# DSD initial price: $0.X
lp_initial_usdc = 1000000
lp_initial_dsd  = 11000000
colors = dict({
    "quadratic_tax_uni": "dodgerblue",
    "linear_tax": "mediumorchid",
    "no_tax": "black",
    "no_tax_curve": "black",
    "slippage_tax_uni": "crimson",
    "slippage_tax_curve": "green",
    "quadratic_tax_curve": "orange",
})
alpha_opacity = 0.05
num_iterations = 20



########## CURVE ##################

fig, ax = plt.subplots()

# Curve quadratic tax
for i in range(num_iterations):
    c = Curve(lp_initial_usdc, lp_initial_dsd, A=100)
    trades = [generate_trade(mu, sigma) for x in range(nobs)]
    _ = [c.swap(x, tax_function=quadratic_tax) for x in trades]

    # notes: Average trade is -1000, but DSD prices generally
    # end up increasing because of the burn + slippage working against a seller
    tax_style = 'quadratic_tax_curve'

    ax.plot(
        np.linspace(0,len(trades),len(trades)+1),
        c.history[plot_variate],
        color=colors[tax_style],
        alpha=alpha_opacity,
    )

    if i == 0:
        avg_prices[tax_style] = c.history['prices']
        avg_burns[tax_style] = c.history['burns']
        avg_treasury_balances[tax_style] = c.history['treasury_balances']
    else:
        # accumulate prices, divide by num_iterations after
        avg_prices[tax_style] = np.add(
            avg_prices[tax_style],
            c.history['prices']
        )
        avg_burns[tax_style] = np.add(
            avg_burns[tax_style],
            c.history['burns']
        )
        avg_treasury_balances[tax_style] = np.add(
            avg_treasury_balances[tax_style],
            c.history['treasury_balances']
        )

    if i == (num_iterations - 1):
        # last loop, average over all iterations
        avg_prices[tax_style] = np.divide(
            avg_prices[tax_style],
            num_iterations
        )
        avg_burns[tax_style] = np.divide(
            avg_burns[tax_style],
            num_iterations
        )
        avg_treasury_balances[tax_style] = np.divide(
            avg_treasury_balances[tax_style],
            num_iterations
        )
        # Then plot mean price line with alpha=1
        ax.plot(
            np.linspace(0,nobs,nobs+1),
            avg_prices[tax_style],
            color=colors[tax_style],
            alpha=1,
            linewidth=2,
            linestyle="dotted",
        )



# Curve NO tax
for i in range(num_iterations):
    c = Curve(lp_initial_usdc, lp_initial_dsd, A=100)
    trades = [generate_trade(mu, sigma) for x in range(nobs)]
    _ = [c.swap(x, tax_function=no_tax) for x in trades]

    tax_style = 'no_tax_curve'

    ax.plot(
        np.linspace(0,len(trades),len(trades)+1),
        c.history[plot_variate],
        color=colors[tax_style],
        alpha=alpha_opacity,
    )

    if i == 0:
        avg_prices[tax_style] = c.history['prices']
        avg_burns[tax_style] = c.history['burns']
        avg_treasury_balances[tax_style] = c.history['treasury_balances']
    else:
        # accumulate prices, divide by num_iterations after
        avg_prices[tax_style] = np.add(
            avg_prices[tax_style],
            c.history['prices']
        )
        avg_burns[tax_style] = np.add(
            avg_burns[tax_style],
            c.history['burns']
        )
        avg_treasury_balances[tax_style] = np.add(
            avg_treasury_balances[tax_style],
            c.history['treasury_balances']
        )

    if i == (num_iterations - 1):
        # last loop, average over all iterations
        avg_prices[tax_style] = np.divide(
            avg_prices[tax_style],
            num_iterations
        )
        avg_burns[tax_style] = np.divide(
            avg_burns[tax_style],
            num_iterations
        )
        avg_treasury_balances[tax_style] = np.divide(
            avg_treasury_balances[tax_style],
            num_iterations
        )
        # Then plot mean price line with alpha=1
        ax.plot(
            np.linspace(0,nobs,nobs+1),
            avg_prices[tax_style],
            color=colors[tax_style],
            alpha=1,
            linewidth=2,
            linestyle="dotted",
        )




######### BUGGY ############
######## Curve slippage tax
######### BUGGY ############
# for i in range(num_iterations):
#     c = Curve(lp_initial_usdc, lp_initial_dsd)
#     trades = [generate_trade(mu, sigma) for x in range(nobs)]
#     _ = [c.swap(x, tax_function='slippage') for x in trades]
#
#     # notes: Average trade is -1000, but DSD prices generally
#     # end up increasing because of the burn + slippage working against a seller
#     tax_style = 'slippage_tax_curve'
#
#     ax.plot(
#         np.linspace(0,nobs,nobs+1),
#         c.history[plot_variate],
#         color=colors[tax_style],
#         alpha=alpha_opacity,
#     )
#
#     if i == 0:
#         avg_prices[tax_style] = c.history['prices']
#         avg_burns[tax_style] = c.history['burns']
#         avg_treasury_balances[tax_style] = c.history['treasury_balances']
#     else:
#         # accumulate prices, divide by num_iterations after
#         avg_prices[tax_style] = np.add(
#             avg_prices[tax_style],
#             c.history['prices']
#         )
#         avg_burns[tax_style] = np.add(
#             avg_burns[tax_style],
#             c.history['burns']
#         )
#         avg_treasury_balances[tax_style] = np.add(
#             avg_treasury_balances[tax_style],
#             c.history['treasury_balances']
#         )
#
#     if i == (num_iterations - 1):
#         # last loop, average over all iterations
#         avg_prices[tax_style] = np.divide(
#             avg_prices[tax_style],
#             num_iterations
#         )
#         avg_burns[tax_style] = np.divide(
#             avg_burns[tax_style],
#             num_iterations
#         )
#         avg_treasury_balances[tax_style] = np.divide(
#             avg_treasury_balances[tax_style],
#             num_iterations
#         )
#         # Then plot mean price line with alpha=1
#         ax.plot(
#             np.linspace(0,nobs,nobs+1),
#             avg_prices[tax_style],
#             color=colors[tax_style],
#             alpha=1,
#             linewidth=2,
#             linestyle="dotted",
#         )
# ########## END CURVE ##################




########## START UNISWAP ##################
# quadratic_tax
for i in range(num_iterations):
    u = Uniswap(lp_initial_usdc, lp_initial_dsd)
    trades = [generate_trade(mu, sigma) for x in range(nobs)]
    # _ = [u.swap(x, tax_function=quadratic_tax) for x in trades]
    _ = [u.swap(x, tax_function=quadratic_tax) for x in trades]

    # notes: Average trade is -1000, but DSD prices generally
    # end up increasing because of the burn + slippage working against a seller
    tax_style = 'quadratic_tax_uni'

    ax.plot(
        np.linspace(0,nobs,nobs+1),
        u.history[plot_variate],
        color=colors[tax_style],
        alpha=alpha_opacity,
    )

    if i == 0:
        avg_prices[tax_style] = u.history['prices']
        avg_burns[tax_style] = u.history['burns']
        avg_treasury_balances[tax_style] = u.history['treasury_balances']
    else:
        # accumulate prices, divide by num_iterations after
        avg_prices[tax_style] = np.add(
            avg_prices[tax_style],
            u.history['prices']
        )
        avg_burns[tax_style] = np.add(
            avg_burns[tax_style],
            u.history['burns']
        )
        avg_treasury_balances[tax_style] = np.add(
            avg_treasury_balances[tax_style],
            u.history['treasury_balances']
        )

    if i == (num_iterations - 1):
        # last loop, average over all iterations
        avg_prices[tax_style] = np.divide(
            avg_prices[tax_style],
            num_iterations
        )
        avg_burns[tax_style] = np.divide(
            avg_burns[tax_style],
            num_iterations
        )
        avg_treasury_balances[tax_style] = np.divide(
            avg_treasury_balances[tax_style],
            num_iterations
        )
        # Then plot mean price line with alpha=1
        ax.plot(
            np.linspace(0,nobs,nobs+1),
            avg_prices[tax_style],
            color=colors[tax_style],
            alpha=1,
            linewidth=2,
            linestyle="dotted",
        )




plt.title("Simulating sales taxes on Uniswap vs Curve AMMs")
plt.xlabel("number of trades")
plt.ylabel("Price: DSD/USDC")
# place a text box in upper left in axes coords
ax.text(
    1550, .22,
    r'''
    {runs} runs of {nobs} trades sampled from a
    $X \sim N(\mu=${mu},$\sigma$={sigma}) distribution.

    Initial LP: 1,000,000 USDC / 40,000,000 DSD
    '''.format(runs=4*num_iterations, nobs=nobs, mu=mu, sigma=sigma),
    {'color': 'black', 'fontsize': 8},
    verticalalignment='bottom',
    bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
)


legend_elements = [
    Line2D([0], [0], color=colors['quadratic_tax_uni'], lw=2,
           label=r'$(1-price)^2 \times DSD_{sold}$'),
    Line2D([0], [0], color=colors['quadratic_tax_curve'], lw=2, label=r'Curve quadratic tax'),
    # Line2D([0], [0], color=colors['slippage_tax_curve'], lw=2,
    #        label=r'Curve slippage tax'),
]
ax.legend(handles=legend_elements, loc='lower right')

## Even with a slight negative bias, mean = -100, the burns push the price upward slowly over time





fig, ax = plt.subplots()

for tax_style in ["quadratic_tax_uni", "quadratic_tax_curve"]:
    ax.plot(
        np.linspace(0,nobs,nobs+1),
        avg_treasury_balances[tax_style],
        color=colors[tax_style],
        alpha=1,
        linewidth=2,
        linestyle="dotted",
    )

plt.title("Treasury funds from sales taxes")
plt.xlabel("number of trades")
plt.ylabel("Treasury balance (millions DSD)")
legend_elements = [
    Line2D([0], [0], color=colors['quadratic_tax_uni'], lw=2,
           label=r'Uniswap quadratic tax'),
    Line2D([0], [0], color=colors['quadratic_tax_curve'], lw=2,
           label=r'Curve quadratic tax'),
    # Line2D([0], [0], color=colors['slippage_tax_curve'], lw=2,
    #        label=r'Curve slippage tax'),
]
ax.legend(handles=legend_elements, loc='lower right')





plt.title("Price impact of sales on Curve AMMs with sales taxes")
plt.xlabel("number of trades")
plt.ylabel("Price: DSD/USDC")
# place a text box in upper left in axes coords
ax.text(
    1550, .22,
    r'''
    {runs} runs of {nobs} trades sampled from a
    $X \sim N(\mu=${mu},$\sigma$={sigma}) distribution.

    Initial LP: 1,000,000 USDC / 11,000,000 DSD
    '''.format(runs=4*num_iterations, nobs=nobs, mu=mu, sigma=sigma),
    {'color': 'black', 'fontsize': 8},
    verticalalignment='bottom',
    bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
)


legend_elements = [
    # Line2D([0], [0], color=colors['quadratic_tax_uni'], lw=2,
    #        label=r'$(1-price)^2 \times DSD_{sold}$'),
    Line2D([0], [0], color=colors['quadratic_tax_curve'], lw=2, label=r'Curve quadratic tax'),
    Line2D([0], [0], color=colors['no_tax_curve'], lw=2,
           label=r'Curve no tax'),
]
ax.legend(handles=legend_elements, loc='upper right')

