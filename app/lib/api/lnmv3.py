from typing import Literal

from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.v3.models.futures_data import GetCandlesParams, GetFundingSettlementsParams
from lnmarkets_sdk.v3.models.futures_isolated import (
    CloseTradeParams,
    FuturesOrder,
    GetClosedTradesParams,
    GetIsolatedFundingFeesParams,
)
from lnmarkets_sdk.v3.models.oracle import GetLastPriceParams

from app.core.logging import logger

# ---------------------------------------------------------
# LNMarket V3: https://api.lnmarkets.com/v3/
# ---------------------------------------------------------


class LNMV3PublicAPI:
    async def get_oracle_last_price():
        config = APIClientConfig(network="mainnet", timeout=60.0)
        async with LNMClient(config) as client:
            params = GetLastPriceParams(limit=1)
            oracle_last_price = await client.oracle.get_last_price(params)
            return oracle_last_price


class LNMV3SDK:
    config = None
    account = {}
    running_trades = []
    open_trades = []
    closed_trades = []

    def __init__(self, key: str, secret: str, passphrase: str, network: str = "mainnet"):
        self.config = APIClientConfig(
            authentication=APIAuthContext(key=key, secret=secret, passphrase=passphrase),
            network=network,
            timeout=60.0,
        )

    async def refresh_account(self):
        async with LNMClient(self.config) as client:
            self.account = await client.account.get_account()
            return self.account

    async def get_ticker(self):
        async with LNMClient(self.config) as client:
            result = await client.futures.get_ticker()
            return result

    async def get_leaderboard(self):
        async with LNMClient(self.config) as client:
            result = await client.futures.get_leaderboard()
            return result

    async def get_lightning_deposits(self):
        async with LNMClient(self.config) as client:
            result = await client.account.get_lightning_deposits()
            return result

    async def get_internal_deposits(self):
        async with LNMClient(self.config) as client:
            result = await client.account.get_internal_deposits()
            return result

    async def get_on_chain_deposits(self):
        async with LNMClient(self.config) as client:
            result = await client.account.get_on_chain_deposits()
            return result

    async def refresh_running_trades(self):
        async with LNMClient(self.config) as client:
            self.running_trades = await client.futures.isolated.get_running_trades()
            return self.running_trades

    async def refresh_open_trades(self):
        async with LNMClient(self.config) as client:
            self.open_trades = await client.futures.isolated.get_open_trades()
            return self.open_trades

    async def refresh_closed_trades(self, limit: int = 50):
        async with LNMClient(self.config) as client:
            params = GetClosedTradesParams(limit=limit)
            response = await client.futures.isolated.get_closed_trades(params)
            self.closed_trades = response.data
            return self.closed_trades

    async def get_funding_fees(self):
        async with LNMClient(self.config) as client:
            isolated_fees = await client.futures.isolated.get_funding_fees(GetIsolatedFundingFeesParams(limit=5))
            return isolated_fees

    async def total_net_value(self):
        await self.refresh_account()
        await self.refresh_running_trades()
        trades = []
        for trade in self.running_trades:
            initial_margin = trade.margin
            maint_margin = trade.maintenance_margin
            pl = trade.pl
            opening_fee = trade.opening_fee
            trades.append(initial_margin + maint_margin + pl + opening_fee)
        trades_total = sum(item for item in trades)
        total = trades_total + self.account.balance
        return total

    async def get_funding_settlements(self):
        async with LNMClient(self.config) as client:
            funding_settlements = await client.futures.get_funding_settlements(GetFundingSettlementsParams(limit=5))
            return funding_settlements

    async def get_oracle_index(self, limit: int = 1):
        async with LNMClient(self.config) as client:
            params = GetLastPriceParams(limit=limit)
            oracle_index = await client.oracle.get_index(params)
            return oracle_index

    async def get_oracle_last_price(self):
        async with LNMClient(self.config) as client:
            oracle_last_price = await client.oracle.get_last_price()
            return oracle_last_price

    async def ping(self):
        async with LNMClient(self.config) as client:
            ping_response = await client.ping()
            return ping_response

    async def server_time(self):
        async with LNMClient(self.config) as client:
            time_response = await client.time()
            return time_response

    async def cancel_all(self):
        async with LNMClient(self.config) as client:
            response = await client.futures.isolated.cancel_all()
            return response

    async def close_all(self):
        running_trades = await self.refresh_running_trades()
        logger.info(f"   closing all {len(running_trades)}...")
        if len(running_trades):
            async with LNMClient(self.config) as client:
                responses = []
                logger.info(f"   type= {type(running_trades)}")
                logger.info(f"   total= {len(running_trades)}")
                for trade in running_trades:
                    try:
                        params = CloseTradeParams(id=trade.id)
                        response = await client.futures.isolated.close(params)
                        responses.append({"trade": trade, "response": response})
                    except Exception as e:
                        logger.info(f"   error to close {trade.id} -> ERROR: {e}")
                return responses
        else:
            return []

    async def get_candles(self, range: str = "1h", limit: int = 10):
        async with LNMClient(self.config) as client:
            dfrom = "2024-01-01T00:00:00.000Z"
            candles_params = GetCandlesParams(from_=dfrom, range=range, limit=limit)
            candles = await client.futures.get_candles(candles_params)
            return candles.data

    async def new_trade(
        self,
        side: Literal["limit", "market"] = "buy",
        quantity: int = 1,
        leverage: int = 1,
        stoploss: float | None = None,
        takeprofit: float | None = None,
    ):
        async with LNMClient(self.config) as client:
            params = FuturesOrder(
                type="market",  # limit order
                side=side,  # buy
                quantity=quantity,
                leverage=leverage,
                stoploss=stoploss,  # optional stop loss
                takeprofit=takeprofit,  # optional take profit
            )
            response = await client.futures.isolated.new_trade(params)
            return response
