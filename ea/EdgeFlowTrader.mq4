//+------------------------------------------------------------------+
//| EdgeFlow Trader EA  v0.2 - Fixed                                 |
//+------------------------------------------------------------------+
#property strict
#property copyright "EdgeFlow"
#property link      "https://github.com/AgentMrBig/EdgeFlow-Trader"

#include <stdlib.mqh>

input int      FlushSeconds = 5;
input int      MagicNumber  = 12345;
input color    OrderColor   = clrBlue;

string TickFile = "ticks.csv";
string OrderFile = "orders.json";
string ExecFile  = "executions.csv";
datetime lastFlush = 0;

//+------------------------------------------------------------------+
//| Helper to strip quotes and whitespace from a JSON string field   |
//+------------------------------------------------------------------+
string Extract(string json, string key)
{
   string pat = "\"" + key + "\"";
   int p = StringFind(json, pat);
   if (p == -1) return "";
   p = StringFind(json, ":", p) + 1;
   int q = StringFind(json, ",", p);
   int e = StringFind(json, "}", p);
   if (q == -1 || (e != -1 && e < q)) q = e;
   string raw = StringSubstr(json, p, q - p);

   // Trim leading/trailing whitespace manually
   while (StringLen(raw) > 0 && StringGetChar(raw, 0) <= ' ')
      raw = StringSubstr(raw, 1);
   while (StringLen(raw) > 0 && StringGetChar(raw, StringLen(raw) - 1) <= ' ')
      raw = StringSubstr(raw, 0, StringLen(raw) - 1);

   // Remove quotes and "null"
   raw = StringReplace(raw, "\"", "");
   raw = StringReplace(raw, "null", "");

   return raw;
}

//+------------------------------------------------------------------+
int OnInit()
{
   int fh = FileOpen(TickFile, FILE_CSV | FILE_READ | FILE_WRITE, ',');
   if (FileSize(fh) == 0)
      FileWrite(fh, "time,bid,ask,spread");
   FileClose(fh);
   Print("EdgeFlow EA v0.2 initialised.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnTick()
{
   logTick();

   if (!FileIsExist(OrderFile)) return;
   int ofh = FileOpen(OrderFile, FILE_READ | FILE_SHARE_READ);
   if (ofh < 0) return;

   string j = FileReadString(ofh);
   FileClose(ofh);
   FileDelete(OrderFile);

   if (StringLen(j) < 10) return;

   string symbol = Extract(j, "symbol");
   string side   = Extract(j, "side");
   string lotS   = Extract(j, "lot");
   string slS    = Extract(j, "sl");
   string tpS    = Extract(j, "tp");
   string slipS  = Extract(j, "slippage");

   if (symbol == "" || side == "" || lotS == "") {
      Print("Bad JSON:", j);
      return;
   }

   double lot = StrToDouble(lotS);
   double sl  = (slS == "") ? 0 : StrToDouble(slS);
   double tp  = (tpS == "") ? 0 : StrToDouble(tpS);
   int slip   = (slipS == "") ? 3 : (int)StrToInteger(slipS);

   int cmd = (StringFind(side, "buy") == 0) ? OP_BUY : OP_SELL;
   double price = (cmd == OP_BUY) ? Ask : Bid;

   int ticket = OrderSend(symbol, cmd, lot, price, slip, sl, tp,
                          "EdgeFlow", MagicNumber, 0, OrderColor);

   if (ticket > 0) {
      logExecution(ticket, symbol, side, lot, price);
      PrintFormat("EXECUTED ticket=%d lot=%.2f at %.5f", ticket, lot, price);
   } else {
      PrintFormat("ORDER FAIL err=%d", GetLastError());
   }
}

//+------------------------------------------------------------------+
void logTick()
{
   double bid = MarketInfo(Symbol(), MODE_BID);
   double ask = MarketInfo(Symbol(), MODE_ASK);
   double spr = (ask - bid) / Point;

   string ts = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
   StringReplace(ts, ".", "-");

   int fh = FileOpen(TickFile, FILE_CSV | FILE_READ | FILE_WRITE | FILE_SHARE_WRITE, ',');
   FileSeek(fh, 0, SEEK_END);
   FileWrite(fh, ts,
                 DoubleToString(bid, _Digits),
                 DoubleToString(ask, _Digits),
                 DoubleToString(spr, 1));
   if (TimeCurrent() - lastFlush >= FlushSeconds) {
      FileFlush(fh);
      lastFlush = TimeCurrent();
   }
   FileClose(fh);
}

//+------------------------------------------------------------------+
void logExecution(int ticket, string sym, string side, double lot, double price)
{
   int fh = FileOpen(ExecFile, FILE_CSV | FILE_READ | FILE_WRITE | FILE_SHARE_WRITE, ',');
   if (FileSize(fh) == 0)
      FileWrite(fh, "ticket,time,symbol,side,lot,price");

   FileSeek(fh, 0, SEEK_END);
   string ts = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
   StringReplace(ts, ".", "-");
   FileWrite(fh, ticket, ts, sym, side, lot, price);
   FileFlush(fh);
   FileClose(fh);
}
//+------------------------------------------------------------------+
