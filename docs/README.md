# EdgeFlow Trader — Sprint-0 Quick-Start

1. **Compile & attach the EA**  
   *MetaEditor → open `ea/EdgeFlowTrader.mq4` → Compile → attach to a USDJPY M1 chart.*

2. **Start database**  
   ```bash
   docker compose -f docker/timescaledb-compose.yml up -d
