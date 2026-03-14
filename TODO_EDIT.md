# Edit Dataset - Add Row Feature

**Information Gathered**:
- templates/edit.html: Inline editable table, POST updates existing rows
- app.py /edit: Loops i in 0..len(data_df), updates data_df.at[i,col], no new rows
- Goal: "Add Row" button in Edit → JS append empty row → POST appends to data_df

**Plan**:
1. [x] templates/edit.html: "➕ Add Row" button + JS dynamic row creation/population
2. [x] app.py /edit POST: Handles new rows (resize df + update)

3. Re-process_data() + redirect dashboard
4. Test: Edit → Add Row → fill → Save → new row in dashboard table

**Dependent**: templates/edit.html, app.py

**Followup**: Save to data/needbe/updated_sample.csv? Confirm.

Ready to proceed?

