//+------------------------------------------------------------------+
//| EdgeFlow Trader EA  v0.1                                         |
//| Logs every tick to CSV and listens for order JSON commands       |
//+------------------------------------------------------------------+
#property copyright "EdgeFlow Trader"
#property link      "https://github.com/AgentMrBig/EdgeFlow-Trader"
#property strict

#include <stderror.mqh>
#include <stdlib.mqh>

input int   FlushSeconds = 5;          // how often to flush file buffer
string      TickFile    = "ticks.csv";
string      OrderFile   = "orders.json";
datetime    lastFlush   = 0;

//------------------------------------------------------------------+
int OnInit()
{
   // write header once
   int fh = FileOpen(TickFile, FILE_CSV|FILE_READ|FILE_WRITE, ',');
   if(FileSize(fh)==0)
      FileWrite(fh,"time,bid,ask,spread");
   FileClose(fh);
   Print("EdgeFlowTrader EA initialised.");
   return(INIT_SUCCEEDED);
}
//------------------------------------------------------------------+
void OnTick()
{
   double bid = MarketInfo(Symbol(), MODE_BID);
   double ask = MarketInfo(Symbol(), MODE_ASK);
   double spr = (ask-bid)/Point;

   int fh = FileOpen(TickFile, FILE_CSV|FILE_READ|FILE_WRITE|FILE_SHARE_WRITE, ',');
   FileSeek(fh,0,SEEK_END);
   FileWrite(fh,TimeToString(TimeCurrent(),TIME_SECONDS),bid,ask,spr);
   if(TimeCurrent()-lastFlush >= FlushSeconds){ FileFlush(fh); lastFlush=TimeCurrent(); }
   FileClose(fh);

   // --- check for new order command ---
   if(FileIsExist(OrderFile))
   {
      string j = FileReadString(OrderFile,FileSize(OrderFile));
      Print("[EdgeFlow] ORDER RECEIVED → ",j);        // v0.1: echo only
      FileDelete(OrderFile);
   }
}
//------------------------------------------------------------------+
