import backtrader as bt
import Log_Func
class Buy_And_Sell_Strategy(bt.Strategy):

    def buy_function(self, line, size):
        bpk1 = (self.diff[line][-1] <= self.dea[line][-1])
        bpk2 = (self.diff[line][0] > self.dea[line][0])
        if (bpk1 and bpk2):
            if self.broker.getcash() > 0:  # 没有持仓，直接开多头
                Log_Func.Log.log(self, f'OPEN LONG CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.buy(data=line, size=size)

        else:
            pass

    def sell_function(self, line, size):
        spk1 = (self.diff[line][-1] > self.dea[line][-1])
        spk2 = (self.diff[line][0] <= self.dea[line][0])
        if (spk1 and spk2):
            if self.broker.getcash() > 0:  # 持有多头，先平多再开空头
                Log_Func.Log.log(self, f'CLOSE LONG POSITION,{line._name},Size:{size},Price:{line.close[0]:.2f}')
                self.close(data=line)
                Log_Func.Log.log(self, f'OPEN SHORT CREATE AFTER CLOSING LONG, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.sell(data=line, size=size)

    def open_short_function(self, line, size):
        """
        没有持仓，直接开空头
        """
        spk1 = (self.diff[line][-1] > self.dea[line][-1])
        spk2 = (self.diff[line][0] <= self.dea[line][0])
        if (spk1 and spk2):
            if self.broker.getcash() > 0:
                Log_Func.Log.log(self, f'OPEN SHORT CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.sell(data=line, size=size)

    def close_short_function(self, line, size):
        """
        持有空头,平空并买入
        """
        bpk1=(self.diff[line][-1]<=self.dea[line][-1])
        bpk2=(self.diff[line][0]>self.dea[line][0])
        if(bpk1 and bpk2):
            pos=self.getposition(line).size
            if self.broker.getcash()>0:
                Log_Func.Log.log(self,f'CLOSE SHORT CREATE, {line._name}, Size: {pos}, Price: {line.close[0]:.2f}')
                self.close(data=line)
                Log_Func.Log.log(self,f'BUY CREATE, {line._name}, Size: {size}, Price: {line.close[0]:.2f}')
                self.buy(data=line,size=size)
        else:
            pass


