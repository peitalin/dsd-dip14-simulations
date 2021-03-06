
import numpy as np
import pandas as pd
# plots
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplfinance as fplt




class Uniswap:
    "This is a Uniswap AMM"

    def __init__(self,
        x=1200,
        y=400,
        x_name="USDC",
        y_name="DSD",
        treasury_tax_rate=0.5
    ):
        # x, y are initial balances
        self.balance_x = x
        self.balance_y = y
        self.x_name = x_name
        self.y_name = y_name
        self.k = x * y # invariant
        # for more on how AMMs work:
        # https://uniswap.org/docs/v2/protocol-overview/how-uniswap-works/
        self.history = dict({
            # history of treasury balances over time
            'treasury_balances': [0],
            # history of prices
            'prices': [self.price_oracle()], # initial price
            # history of burns over time
            'burns': [0],
        })
        self.ohlc = None
        self.treasury_tax_rate=0.5


    def __repr__(self):
        treasury_balance = self.history['treasury_balances'][-1]
        return """
        Liquidity Pool:
        {x_name} balance:\t{balance_x:>12.4f}
        {y_name} balance:\t{balance_y:>12.4f}
        {y_name}/{x_name} price: {price:.10f}

        DAO Treasury from sales taxes:
        {y_name} balance: {treasury_balance:>12.4f}
        """.format(
            x_name = self.x_name,
            balance_x = self.balance_x,
            y_name = self.y_name,
            balance_y = self.balance_y,
            price = self.price_oracle(),
            treasury_balance = treasury_balance
        )


    def ohlc_generate_prices(self, num_sections=10):
        # split history['prices'] into arrays [[], []]
        ts_prices = np.array_split(self.history['prices'], num_sections)
        dates = pd.date_range(start='1/1/2021', periods=len(ts_prices))
        ohlc_timeseries = []

        for i, ts in enumerate(ts_prices):
            ohlc_timeseries.append(dict({
                'Date': dates[i],
                'Open': ts[0],
                'High': np.max(ts),
                'Low': np.min(ts),
                'Close': ts[-1],
            }))
        # dates = pd.date_range(start='1/1/2021', end='1/2/2021', periods=1000)
        ohlc_df = pd.DataFrame(ohlc_timeseries)
        self.ohlc = ohlc_df.set_index("Date")
        return self.ohlc


    def ohlc_plot(self, num_sections=10):
        self.ohlc_generate_prices(num_sections)
        fplt.plot(
            self.ohlc,
            type='candle',
            style='yahoo',
            title='DSD, simulated trades',
            ylabel='Price DSD/USDC'
        )


    def show_balances(self):
        print("{} balance:\t{}".format(self.x_name, self.balance_x))
        print("{} balance:\t{}".format(self.y_name, self.balance_y))


    def show_price(self):
        print("{y_name}/{x_name} price: {price}".format(
            x_name = self.x_name,
            y_name = self.y_name,
            price = self.price_oracle(),
        ))


    def price_oracle(self):
        return self.balance_x / self.balance_y


    def swap(self, trade, tax_function):
        """
        trade: dict({ 'type': 'sell'|'buy', amount: float })
        """

        if trade['type'] == 'buy':
            price_after = self.buy_dsd(trade['amount'])
        else:
            if tax_function == "slippage":
                price_after = self.sell_dsd_slippage_tax(trade['amount'])
            else:
                price_after = self.sell_dsd(trade['amount'], tax_function)

        # self.show_balances()
        # self.show_price()
        return price_after


    def buy_dsd_with_usdc(self, usdc_amount):
        """Buys usdc_amount worth of DSD
        Denominated in USDC
        no taxes for buys"""

        new_x = self.balance_x + usdc_amount
        y = uniswap_y(new_x, self.k)
        self.balance_x = new_x
        self.balance_y = y

        self.history['treasury_balances'].append(
            self.history['treasury_balances'][-1]
        ) # no change to treasury on buys
        self.history['prices'].append(self.price_oracle())
        self.history['burns'].append(0)
        return self.price_oracle()


    def buy_dsd(self, dsd_amount):
        """Buys DSD, denominated in DSD
        no taxes for buys"""

        new_y = self.balance_y - dsd_amount
        x = uniswap_x(new_y, self.k)
        self.balance_x = x
        self.balance_y = new_y

        self.history['treasury_balances'].append(
            self.history['treasury_balances'][-1]
        ) # no change to treasury on buys
        self.history['prices'].append(self.price_oracle())
        self.history['burns'].append(0) # no burns on buys
        return self.price_oracle()


    def sell_dsd(self,
             dsd_amount,
             tax_function=lambda *args, **kwargs: 0
         ):
        """Sells dsd_amount worth of DSD
        Sales tax style: quadratic with distance from peg
        ($1 - price) * DSD
        """
        # plt.plot(np.linspace(0,1,100), [(1 - x**2) for x in np.linspace(1,0,100)])

        prior_balance_x = self.balance_x
        prior_balance_y = self.balance_y
        prior_price = self.price_oracle()

        # Calculate DSD burn before updating balances
        # Or after? After might be better as it takes into account the size of the sell order (slippage)
        burn = tax_function(
            price=prior_price,
            dsd_amount=np.abs(dsd_amount)
        )

        # actual amount sold into LP pool after burn
        leftover_dsd = np.abs(dsd_amount) - burn
        assert leftover_dsd >= 0

        # print('leftover_dsd:', leftover_dsd)
        # print('self.balance_y:', self.balance_y + leftover_dsd)
        x = uniswap_x(self.balance_y + leftover_dsd, self.k)
        after_balance_x = x
        after_balance_y = self.balance_y + leftover_dsd

        # calculate burn first, update balances
        self.balance_y = after_balance_y
        self.balance_x = after_balance_x
        after_price = self.price_oracle()

        # fraction of burnt dsd, to treasury, say 50%
        burn_to_treasury = self.treasury_tax_rate * burn
        actual_burn = (1 - self.treasury_tax_rate) * burn

        self.history['treasury_balances'].append(
            self.history['treasury_balances'][-1] + burn_to_treasury
        )
        self.history['prices'].append(after_price)
        self.history['burns'].append(actual_burn)

        return self.price_oracle()



    def sell_dsd_slippage_tax(self, dsd_amount):
        """Sells dsd_amount worth of DSD
        sales taxes are scaled by slippage imparted to AMM curve
        """
        # this needs its own function as you need to calculate slippage first, before calculating burn and updating pool balances
        # unlike the other simple price-based sales taxes

        dsd = np.abs(dsd_amount)
        prior_balance_x = self.balance_x
        prior_balance_y = self.balance_y
        prior_price = self.price_oracle()

        # balance_y (DSD) increases when DSD is sold to pool
        after_balance_x = uniswap_x(
            prior_balance_y + dsd,
            self.k
        )
        after_balance_y = self.balance_y + dsd

        # calculate slippage + burn first, before swap
        slippage = dydx_once(
            x2 = after_balance_y,
            x1 = prior_balance_y,
            y2 = after_balance_x,
            y1 = prior_balance_x,
        )
        burn =  (1 - np.abs(slippage)) * dsd if (np.abs(slippage) < 1) else 0
        # print("burn: {}".format(1 - slippage))
        # print("price: {}".format(prior_price))
        print("slippage: {}".format(slippage))

        # actual amount sold into LP pool after burn
        leftover_dsd = dsd - burn

        # now update calculate burn-adjusted balance for x
        after_balance_x = uniswap_x(
            prior_balance_y + leftover_dsd,
            self.k
        )

        # now update balances adjusting for burn
        self.balance_y = after_balance_y
        self.balance_x = after_balance_x
        after_price = self.price_oracle()

        # fraction of sales taxes paid to treasury
        burn_to_treasury = self.treasury_tax_rate * burn
        actual_burn = (1 - self.treasury_tax_rate) * burn

        self.history['treasury_balances'].append(
            self.history['treasury_balances'][-1] + burn_to_treasury
        )
        self.history['prices'].append(after_price)
        self.history['burns'].append(actual_burn)

        return self.price_oracle()




#### Invariants ####
## work out balance of token X in a pool, given Y
## holding invariant constant

def uniswap_y(x, k=250):
    y = k/x
    assert not np.isnan(y)
    assert y >= 0
    return y


def uniswap_x(y, k=250):
    x = k/y
    if np.isnan(x):
        print('x: ', x)
        print('y: ', y)
    assert not np.isnan(x)
    if (x < 0):
        print('x: ', x)
        print('y: ', y)
    assert x >= 0
    return x


def linear_y(x, k=250):
    y = k - x
    assert not np.isnan(y)
    assert y >= 0
    return y


def dydx_once(y2, y1, x2, x1):
    """calculates derivative for dy relative to dx"""
    # Needed to figure out dUSDC/dDSD slippage/price impact
    return np.diff([y2, y1])[0] / np.diff([x2, x1])[0]
