# Analytics Studio - Step-by-Step Usage Guide

This guide walks you through using Analytics Studio from start to finish with real examples.

## 🎯 Prerequisites

- Server running at `http://localhost:8000`
- Access to API documentation at `http://localhost:8000/docs`
- A web browser or API client (curl, Postman, etc.)

---

## Step 1: Explore the API Documentation

1. **Open your browser** and navigate to:
   ```
   http://localhost:8000/docs
   ```

2. **You'll see**:
   - All available API endpoints organized by category
   - Interactive forms to test each endpoint
   - Request/response schemas
   - Try it out functionality

3. **Test the health endpoint**:
   - Click on `GET /health`
   - Click "Try it out"
   - Click "Execute"
   - You should see: `{"status":"healthy","service":"Analytics Studio","version":"0.1.0"}`

---

## Step 2: Register Your First Dataset

A dataset represents a table in your database that contains analytics data.

### Using the API Docs (Recommended for beginners):

1. **Navigate to** `POST /api/v1/datasets` in the docs
2. **Click "Try it out"**
3. **Fill in the request body**:
   ```json
   {
     "id": "sales_data",
     "name": "Sales Data",
     "table_name": "sales_fact",
     "grain": "daily",
     "description": "Daily sales transactions",
     "schema_name": null
   }
   ```
4. **Click "Execute"**
5. **You should see** a 201 response with the created dataset

### Using curl (Command line):

```bash
curl -X POST "http://localhost:8000/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sales_data",
    "name": "Sales Data",
    "table_name": "sales_fact",
    "grain": "daily",
    "description": "Daily sales transactions"
  }'
```

### Expected Response:
```json
{
  "id": "sales_data",
  "name": "Sales Data",
  "description": "Daily sales transactions",
  "table_name": "sales_fact",
  "schema_name": null,
  "grain": "daily",
  "is_active": true,
  "created_at": "2026-01-22T15:00:00",
  "updated_at": "2026-01-22T15:00:00"
}
```

---

## Step 3: Define a Semantic Layer

The semantic layer defines what dimensions and measures are available, and what aggregations are allowed.

### Example: Sales Data Semantic Layer

1. **Navigate to** `POST /api/v1/semantic/validate` in the docs
2. **Click "Try it out"**
3. **Fill in the request body**:
   ```json
   {
     "schema_json": {
       "grain": "daily",
       "time_columns": ["sale_date", "created_at"],
       "dimensions": [
         {
           "name": "region",
           "column": "region_name",
           "type": "string",
           "description": "Geographic region"
         },
         {
           "name": "product_category",
           "column": "category",
           "type": "string",
           "description": "Product category"
         },
         {
           "name": "customer_segment",
           "column": "segment",
           "type": "string",
           "description": "Customer segment"
         }
       ],
       "measures": [
         {
           "name": "revenue",
           "column": "amount",
           "type": "numeric",
           "aggregations": ["SUM", "AVG", "MIN", "MAX"],
           "format": "currency",
           "description": "Sales revenue"
         },
         {
           "name": "quantity",
           "column": "qty",
           "type": "numeric",
           "aggregations": ["SUM", "AVG", "COUNT"],
           "description": "Quantity sold"
         },
         {
           "name": "order_count",
           "column": "order_id",
           "type": "numeric",
           "aggregations": ["COUNT", "DISTINCT_COUNT"],
           "description": "Number of orders"
         }
       ]
     }
   }
   ```
4. **Click "Execute"**
5. **You should see**:
   ```json
   {
     "is_valid": true,
     "error_message": null,
     "ui_fields": {
       "dimensions": [...],
       "measures": [...],
       "time_columns": ["sale_date", "created_at"],
       "grain": "daily"
     },
     "validation_rules": {...}
   }
   ```

### Parse Semantic to UI Fields:

1. **Navigate to** `POST /api/v1/semantic/parse`
2. **Use the same schema_json** from above
3. **Click "Execute"**
4. **You'll get** UI-ready field definitions that can be used in the frontend

---

## Step 4: Validate a Calculation Formula

Before creating calculated measures, validate your formulas.

### Example: Calculate Profit Margin

1. **Navigate to** `POST /api/v1/calculations/validate`
2. **Fill in the request body**:
   ```json
   {
     "formula": "(revenue - cost) / revenue * 100",
     "available_fields": ["revenue", "cost", "quantity", "region"]
   }
   ```
3. **Click "Execute"**
4. **You should see**:
   ```json
   {
     "is_valid": true,
     "error_message": null,
     "validation_result": {
       "formula": "(revenue - cost) / revenue * 100",
       "is_valid": true,
       "fields_used": ["revenue", "cost"]
     }
   }
   ```

### Example: Invalid Formula (Nested Aggregations)

Try this invalid formula:
```json
{
  "formula": "SUM(AVG(revenue))",
  "available_fields": ["revenue"]
}
```

**Result**: `is_valid: false` with error message about nested aggregations

### Check for Division by Zero:

1. **Navigate to** `POST /api/v1/calculations/check-division-by-zero`
2. **Fill in**:
   ```json
   {
     "formula": "revenue / quantity"
   }
   ```
3. **You'll get** a warning if division by zero is possible

---

## Step 5: Execute a Query

Now let's query your data! This is where the magic happens.

### Example: Get Revenue by Region

1. **Navigate to** `POST /api/v1/query/execute`
2. **Fill in the request body**:
   ```json
   {
     "dataset_id": "sales_data",
     "dimensions": ["region"],
     "measures": [
       {
         "name": "revenue",
         "column": "amount",
         "aggregation": "SUM",
         "alias": "total_revenue"
       }
     ],
     "filters": null,
     "time_filter": {
       "column": "sale_date",
       "start_date": "2024-01-01",
       "end_date": "2024-12-31"
     },
     "limit": 100
   }
   ```
3. **Click "Execute"**
4. **You'll get**:
   ```json
   {
     "query": "SELECT region, SUM(amount) AS total_revenue FROM \"sales_fact\" WHERE sale_date >= '2024-01-01' AND sale_date <= '2024-12-31' GROUP BY region LIMIT 100",
     "results": [
       {"region": "North America", "total_revenue": 1500000.00},
       {"region": "Europe", "total_revenue": 1200000.00},
       {"region": "Asia", "total_revenue": 900000.00}
     ],
     "row_count": 3
   }
   ```

### Example: Multi-Dimensional Query

```json
{
  "dataset_id": "sales_data",
  "dimensions": ["region", "product_category"],
  "measures": [
    {
      "name": "revenue",
      "column": "amount",
      "aggregation": "SUM",
      "alias": "total_revenue"
    },
    {
      "name": "quantity",
      "column": "qty",
      "aggregation": "SUM",
      "alias": "total_quantity"
    }
  ],
  "filters": [
    {
      "column": "region",
      "operator": "=",
      "value": "North America"
    }
  ],
  "time_filter": {
    "column": "sale_date",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "limit": 50
}
```

### Example: Using IN Filter

```json
{
  "dataset_id": "sales_data",
  "dimensions": ["customer_segment"],
  "measures": [
    {
      "name": "revenue",
      "column": "amount",
      "aggregation": "SUM",
      "alias": "total_revenue"
    }
  ],
  "filters": [
    {
      "column": "region",
      "operator": "IN",
      "value": ["North America", "Europe"]
    }
  ],
  "limit": 100
}
```

---

## Step 6: Create a Dashboard

Dashboards combine multiple visuals into a single view.

### Example: Sales Dashboard

1. **Navigate to** `POST /api/v1/dashboards`
2. **Fill in the request body**:
   ```json
   {
     "name": "Sales Overview Dashboard",
     "description": "Key sales metrics and trends",
     "layout_config": {
       "columns": 12,
       "rows": 8,
       "cell_height": 100
     },
     "visuals": [
       {
         "visual_type": "kpi",
         "config": {
           "measure": {
             "name": "revenue",
             "column": "amount",
             "aggregation": "SUM",
             "alias": "total_revenue"
           },
           "filters": [],
           "time_filter": {
             "column": "sale_date",
             "start_date": "2024-01-01",
             "end_date": "2024-12-31"
           }
         },
         "position": {
           "x": 0,
           "y": 0,
           "width": 3,
           "height": 2
         },
         "order": 0
       },
       {
         "visual_type": "line",
         "config": {
           "dimensions": ["sale_date"],
           "measures": [
             {
               "name": "revenue",
               "column": "amount",
               "aggregation": "SUM",
               "alias": "daily_revenue"
             }
           ],
           "filters": [],
           "time_filter": {
             "column": "sale_date",
             "start_date": "2024-01-01",
             "end_date": "2024-12-31"
           },
           "time_grain": "daily",
           "sorting": {
             "field": "sale_date",
             "order": "asc"
           }
         },
         "position": {
           "x": 3,
           "y": 0,
           "width": 9,
           "height": 4
         },
         "order": 1
       },
       {
         "visual_type": "bar",
         "config": {
           "dimensions": ["region"],
           "measures": [
             {
               "name": "revenue",
               "column": "amount",
               "aggregation": "SUM",
               "alias": "revenue_by_region"
             }
           ],
           "filters": [],
           "time_filter": {
             "column": "sale_date",
             "start_date": "2024-01-01",
             "end_date": "2024-12-31"
           },
           "sorting": {
             "field": "revenue_by_region",
             "order": "desc"
           }
         },
         "position": {
           "x": 0,
           "y": 4,
           "width": 6,
           "height": 4
         },
         "order": 2
       },
       {
         "visual_type": "table",
         "config": {
           "dimensions": ["region", "product_category"],
           "measures": [
             {
               "name": "revenue",
               "column": "amount",
               "aggregation": "SUM",
               "alias": "total_revenue"
             },
             {
               "name": "quantity",
               "column": "qty",
               "aggregation": "SUM",
               "alias": "total_quantity"
             }
           ],
           "filters": [],
           "time_filter": {
             "column": "sale_date",
             "start_date": "2024-01-01",
             "end_date": "2024-12-31"
           },
           "sorting": {
             "field": "total_revenue",
             "order": "desc"
           },
           "limit": 20
         },
         "position": {
           "x": 6,
           "y": 4,
           "width": 6,
           "height": 4
         },
         "order": 3
       }
     ],
     "is_public": false,
     "dataset_id": "sales_data"
   }
   ```
3. **Click "Execute"**
4. **You'll get** the created dashboard with all visuals

---

## Step 7: List and View Dashboards

### List All Dashboards:

1. **Navigate to** `GET /api/v1/dashboards`
2. **Click "Try it out"**
3. **Optional parameters**:
   - `skip`: 0 (pagination offset)
   - `limit`: 100 (max results)
4. **Click "Execute"**
5. **You'll see** a list of all dashboards

### Get a Specific Dashboard:

1. **Navigate to** `GET /api/v1/dashboards/{dashboard_id}`
2. **Enter the dashboard ID** (from the list above)
3. **Click "Execute"**
4. **You'll get** the full dashboard configuration

---

## Step 8: View Changelog

Track all changes made to the system.

### Get All Changelog Entries:

1. **Navigate to** `GET /api/v1/changelog`
2. **Optional filters**:
   - `entity_type`: Filter by entity type (dataset, dashboard, etc.)
   - `entity_id`: Filter by specific entity
   - `change_type`: Filter by change type
   - `skip`: Pagination offset
   - `limit`: Max results
3. **Click "Execute"**
4. **You'll see** all changelog entries

### Get Entity History:

1. **Navigate to** `GET /api/v1/changelog/entity/{entity_type}/{entity_id}`
2. **Example**: `/api/v1/changelog/entity/dataset/sales_data`
3. **You'll get** the complete history for that entity

---

## Step 9: Using curl for Automation

Here are curl examples for common operations:

### Register Dataset:
```bash
curl -X POST "http://localhost:8000/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "inventory_data",
    "name": "Inventory Data",
    "table_name": "inventory_fact",
    "grain": "daily"
  }'
```

### Validate Semantic Schema:
```bash
curl -X POST "http://localhost:8000/api/v1/semantic/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_json": {
      "grain": "daily",
      "time_columns": ["date"],
      "dimensions": [{"name": "warehouse", "column": "warehouse_id", "type": "string"}],
      "measures": [{"name": "stock", "column": "quantity", "type": "numeric", "aggregations": ["SUM", "AVG"]}]
    }
  }'
```

### Execute Query:
```bash
curl -X POST "http://localhost:8000/api/v1/query/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "sales_data",
    "dimensions": ["region"],
    "measures": [{"name": "revenue", "column": "amount", "aggregation": "SUM", "alias": "total"}],
    "limit": 10
  }'
```

---

## Step 10: Common Workflows

### Workflow 1: Complete Analytics Setup

1. **Register Dataset** → `POST /api/v1/datasets`
2. **Validate Semantic Layer** → `POST /api/v1/semantic/validate`
3. **Create Dashboard** → `POST /api/v1/dashboards`
4. **Execute Queries** → `POST /api/v1/query/execute`

### Workflow 2: Data Exploration

1. **List Datasets** → `GET /api/v1/datasets`
2. **Execute Query with Filters** → `POST /api/v1/query/execute`
3. **Refine Query** → Adjust filters and dimensions
4. **Save as Dashboard** → `POST /api/v1/dashboards`

### Workflow 3: Formula Development

1. **Validate Formula** → `POST /api/v1/calculations/validate`
2. **Check Division by Zero** → `POST /api/v1/calculations/check-division-by-zero`
3. **Parse Formula** → `POST /api/v1/calculations/parse`
4. **Use in Query** → Include in query measures

---

## 🎓 Tips & Best Practices

### 1. Always Validate First
- Validate semantic schemas before using them
- Validate formulas before creating calculated measures
- Check field usage before building queries

### 2. Use Meaningful Aliases
When creating measures in queries, use clear aliases:
```json
{
  "name": "revenue",
  "column": "amount",
  "aggregation": "SUM",
  "alias": "total_revenue"  // Clear and descriptive
}
```

### 3. Start Simple
- Begin with single-dimension queries
- Add filters gradually
- Build complex dashboards incrementally

### 4. Leverage Time Filters
Always include time filters for time-series data:
```json
{
  "column": "sale_date",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 5. Use Limits
Always set reasonable limits to avoid large result sets:
```json
{
  "limit": 100  // Prevents overwhelming responses
}
```

---

## 🐛 Troubleshooting

### Issue: "Dataset not found"
**Solution**: Make sure you've registered the dataset first using `POST /api/v1/datasets`

### Issue: "Validation failed"
**Solution**: 
- Check that your semantic schema matches the required format
- Ensure all required fields are present
- Verify field names match your actual database columns

### Issue: "Query execution failed"
**Solution**:
- Verify the dataset exists
- Check that column names match your database
- Ensure filters use correct operators (=, !=, IN, >, <, >=, <=)

### Issue: "Permission denied"
**Solution**: 
- Currently using mock authentication
- In production, ensure you have proper JWT tokens
- Check user roles and permissions

---

## 📚 Next Steps

1. **Explore More Endpoints**: Check out all endpoints in `/docs`
2. **Read Architecture**: See `ARCHITECTURE.md` for system design
3. **Quick Start Guide**: See `QUICKSTART.md` for developer onboarding
4. **Build Frontend**: Use these APIs to build your analytics UI
5. **Add Authentication**: Implement JWT authentication for production

---

## 🎉 You're Ready!

You now know how to:
- ✅ Register datasets
- ✅ Define semantic layers
- ✅ Validate calculations
- ✅ Execute queries
- ✅ Create dashboards
- ✅ Track changes

**Happy analyzing! 📊**


