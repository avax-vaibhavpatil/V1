# Dashboard Documentation Generation Prompt

You are a senior analytics architect and backend-aware product engineer.

## Context

I have already built a sales dashboard. Now I want to formalize and document its architecture so that:
- We clearly understand what level and shape of data is required to power the dashboard
- The same dashboard structure can be reused for multiple purposes by changing configuration and data inputs
- The backend can dynamically generate multiple versions of the same dashboard

Your task is to create THREE separate Markdown (.md) documents.

---

## DOCUMENT 1: Dashboard Architecture

Create a Markdown file named: `dashboard_architecture.md`

### Purpose
Explain the architecture and working of the dashboard from a data-first perspective, so anyone can understand:
- What data is required
- At what granularity the data must exist
- How the dashboard consumes and transforms this data

### Include the following sections:

1. **Overview**
   - Purpose of the dashboard
   - Design philosophy (data-driven, reusable, configuration-based)

2. **Data Layers**
   - Raw data layer (sources, systems, ownership)
   - Processed/aggregated layer
   - Presentation-ready metrics layer

3. **Data Granularity & Dimensions**
   - Time granularity (day/week/month)
   - Organizational hierarchy (company/region/branch/user)
   - Product/customer dimensions (if applicable)

4. **Metrics & KPIs**
   - Types of metrics (counts, sums, ratios, trends)
   - Mandatory vs optional metrics
   - Derived vs raw metrics

5. **Dashboard Components**
   - Charts, tables, filters, scorecards
   - Mapping between components and data requirements

6. **Data Validation & Assumptions**
   - Minimum data required for dashboard to function
   - Fallbacks when data is missing

7. **Summary**
   - What level of data maturity is required to fully utilize this dashboard

---

## DOCUMENT 2: Configuration Management for Multipurpose Usage

Create a Markdown file named: `dashboard_configuration_management.md`

### Purpose
Explain how configuration can be used to make the same dashboard reusable across different use cases, teams, or roles.

### Include the following sections:

1. **Why Configuration-Based Dashboards**
   - Problems with hardcoded dashboards
   - Benefits of configuration-driven design

2. **Types of Configuration**
   - Data configuration (metrics, dimensions, filters)
   - UI configuration (charts, layout, visibility)
   - Role-based configuration (who sees what)
   - Time-based or business-rule configuration

3. **Configuration Structure**
   - Example JSON/YAML-like configuration structure
   - Explanation of each configuration block

4. **Examples**
   - Example 1: Sales Manager dashboard
   - Example 2: Executive summary dashboard
   - Example 3: Product-wise performance dashboard

5. **Config vs Code Boundaries**
   - What should be configurable
   - What should remain fixed in code

6. **Governance & Versioning**
   - Validation of configs
   - Change management and approvals

---

## DOCUMENT 3: Dynamic Dashboard Versioning from Backend

Create a Markdown file named: `dynamic_dashboard_versioning.md`

### Purpose
Analyze how the backend can dynamically create and serve multiple versions of the same dashboard using the same core structure.

### Include the following sections:

1. **Problem Statement**
   - Why multiple dashboard versions are needed
   - Challenges with duplicating dashboards

2. **Concept of a Dashboard Template**
   - Base dashboard definition
   - Reusable components

3. **Backend Architecture**
   - Dashboard definition storage
   - Configuration resolution flow
   - Data query generation logic

4. **Versioning Strategy**
   - Version identifiers
   - Draft vs published dashboards
   - Backward compatibility

5. **Runtime Flow**
   - Request → config resolution → data fetch → response
   - How different users get different versions

6. **Performance & Caching Considerations**
   - Query reuse
   - Pre-aggregation strategies

7. **Risks & Trade-offs**
   - Complexity vs flexibility
   - Debugging and observability

8. **Final Recommendation**
   - Best practices for implementing dynamic dashboard versioning

---

## General Guidelines

- Use clear headings and bullet points
- Keep explanations practical and implementation-oriented
- Do NOT assume any specific tech stack unless required
- Focus on clarity, reusability, and backend feasibility








