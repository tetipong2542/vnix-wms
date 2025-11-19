# Stock Reservation System

## Overview

The Stock Reservation System prevents creating multiple batches that exceed available stock when you create batches more than once per day.

## How It Works

### Stock Model

```python
class Stock:
    qty             # Total stock (from POS import)
    reserved_qty    # Stock reserved for batches
    available_qty   # Property: qty - reserved_qty
```

### Workflow

```
┌────────────────────────────────────────────┐
│ 1. Import Stock from POS (Morning)        │
│    SKU123: qty=100, reserved_qty=0        │
│    Available: 100                          │
└────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ 2. Create Batch R1 (10:00)                │
│    - Needs SKU123: 60 units                │
│    - Check: available=100 ✅ OK            │
│    - Reserve: reserved_qty = 0 + 60 = 60  │
│    - Now available: 100 - 60 = 40          │
└────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ 3. Create Batch R2 (13:00)                │
│    - Needs SKU123: 50 units                │
│    - Check: available=40 ⚠️ WARNING        │
│    - Log warning but allow creation        │
│    - Reserve: reserved_qty = 60 + 50 = 110 │
│    - Now available: 100 - 110 = -10 (!) │
└────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ 4. Next Day Import (Morning)              │
│    - Import fresh stock from POS           │
│    - Reset: reserved_qty = 0               │
│    - Ready for new day!                    │
└────────────────────────────────────────────┘
```

## Benefits

✅ **Prevents Over-allocation**
- Multiple batches per day won't exceed actual stock
- Warnings logged when stock insufficient

✅ **POS Remains Source of Truth**
- Stock import resets reservations
- No conflict with POS inventory

✅ **Simple to Understand**
- Reserved stock = stock temporarily "locked" for batches
- Available stock = what you can actually use

## Configuration

### Current Behavior (Soft Warning)

By default, the system **allows** batch creation even if stock is insufficient, but logs a warning:

```python
# In app.py: create_batch_from_pending()
if stock_warnings:
    app.logger.warning(f"Stock warnings for batch {batch_id}: {stock_warnings}")
    # Batch is created anyway
```

### Strict Mode (Block if Insufficient)

To prevent batch creation when stock is insufficient, uncomment this line:

```python
# In app.py: create_batch_from_pending()
if stock_warnings:
    app.logger.warning(f"Stock warnings for batch {batch_id}: {stock_warnings}")
    raise ValueError(f"Insufficient stock for {len(stock_warnings)} SKUs")  # ← Uncomment this
```

## Viewing Stock Status

### Check Available Stock

```sql
SELECT
    sku,
    qty as total_stock,
    reserved_qty as reserved,
    (qty - COALESCE(reserved_qty, 0)) as available
FROM stocks
WHERE sku = 'SKU123';
```

### Check Reserved Stock by Batch

```sql
SELECT
    b.batch_id,
    o.sku,
    SUM(o.qty) as qty_in_batch
FROM batches b
JOIN order_lines o ON o.batch_id = b.batch_id
WHERE b.created_at >= date('now')  -- Today's batches
GROUP BY b.batch_id, o.sku
ORDER BY b.batch_id, o.sku;
```

## Important Notes

### Daily Reset

⚠️ **Reserved stock is reset to 0 when you import stock from POS**

This is intentional because:
1. POS is the source of truth
2. Import happens once per day (typically morning)
3. Batches created yesterday are already being picked/dispatched

### If You Create Multiple Batches Per Day

**Scenario**: Morning import, then create 3 batches throughout the day

```
09:00 - Import stock: SKU123 = 100
        reserved_qty = 0, available = 100

10:00 - Batch R1: needs 40
        reserved_qty = 40, available = 60

13:00 - Batch R2: needs 35
        reserved_qty = 75, available = 25

16:00 - Batch R3: needs 30
        reserved_qty = 105, available = -5 ⚠️
        Warning logged!
```

### Manual Stock Adjustment

If you need to manually adjust reserved stock:

```sql
-- Reset all reservations
UPDATE stocks SET reserved_qty = 0;

-- Reset specific SKU
UPDATE stocks SET reserved_qty = 0 WHERE sku = 'SKU123';
```

## Troubleshooting

### Q: Reserved stock is negative?
**A**: This shouldn't happen. If it does, run:
```sql
UPDATE stocks SET reserved_qty = 0 WHERE reserved_qty < 0;
```

### Q: Reserved stock is too high?
**A**: Import fresh stock from POS. This will reset all reservations.

### Q: Want to see which batches reserved what?
**A**: Check the audit logs:
```sql
SELECT * FROM audit_logs
WHERE action = 'create_batch'
  AND date(timestamp) = date('now')
ORDER BY timestamp DESC;
```

## Future Enhancements

Potential improvements:
1. **Batch Cancellation**: Auto-release reserved stock when batch is cancelled
2. **Stock Alerts**: Email notification when creating batch with insufficient stock
3. **Dashboard**: Show reserved vs available stock visually
4. **Historical Tracking**: Log all reservation changes in separate table

---

**Last Updated**: 2025-11-19
**Version**: 1.0
