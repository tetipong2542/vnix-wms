# Implementation Plan

## Overview
Implementation tasks for Batch Management UX improvements, organized in logical order to build incrementally from backend to frontend.

## Tasks

- [x] 1. Backend API Development - Quick Create
  - Implement new API endpoints and helper functions for Quick Create functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Create helper function `get_next_run_number()`
  - Write function in `app.py` to calculate next available run number for a platform and date
  - Query existing Batch records filtered by platform and batch_date
  - Return max(run_no) + 1, or 1 if no batches exist
  - _Requirements: 1.2_

- [x] 1.2 Implement `/batch/next-run/<platform>` endpoint
  - Create GET route in `app.py`
  - Call `get_next_run_number()` helper
  - Get pending orders and use existing `compute_batch_summary()` function
  - Return JSON response with batch preview data (next_run, batch_id_preview, pending_count, summary)
  - Handle errors (invalid platform, no pending orders)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.3 Implement `/batch/quick-create/<platform>` endpoint
  - Create POST route in `app.py`
  - Get next run number automatically using `get_next_run_number()`
  - Call existing `create_batch_from_pending()` function
  - Return JSON response with success/error status and redirect URL
  - Add audit logging for quick create action
  - _Requirements: 1.1, 1.4, 1.5, 7.1, 7.2, 7.3_

- [x] 2. Batch List Page - Quick Create Feature
  - Add Quick Create buttons and modal with AJAX functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2.1 Add Quick Create buttons to Batch List page
  - Add "⚡ สร้างเร็ว" button for each platform in pending orders section
  - Disable button if no pending orders for that platform
  - Add modal HTML structure for Quick Create preview
  - _Requirements: 1.1, 1.5_

- [x] 2.2 Implement Quick Create Modal JavaScript
  - Create `loadQuickCreateData(platform)` function with AJAX call to `/batch/next-run/<platform>`
  - Display loading spinner while fetching data
  - Populate modal with preview data (batch_id, carrier summary, shop summary)
  - Handle errors and display error messages
  - Create `confirmQuickCreate(platform)` function for submission
  - Implement AJAX POST to `/batch/quick-create/<platform>`
  - Show loading state on confirm button
  - Handle success response and redirect to batch detail
  - Handle error response and display error message
  - _Requirements: 1.1, 1.2, 1.4, 1.5, 7.1, 7.4, 7.5_

- [x] 2.3 Style Quick Create Modal
  - Improve modal styling with Bootstrap cards and badges
  - Add color-coded carrier badges (SPX=red, Flash=orange, LEX=blue, J&T=green)
  - Format numbers with proper spacing
  - Add warning message about batch locking
  - Ensure responsive design for mobile
  - _Requirements: 3.1, 3.2, 3.3, 6.4_

- [x] 3. Batch List Page - Filtering and Search
  - Add filtering and search capabilities to Batch List
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3.1 Add filter panel UI to Batch List
  - Create filter section above batch table in `templates/batch_list.html`
  - Add search input for Batch ID
  - Add platform dropdown filter (All, Shopee, Lazada, TikTok)
  - Add status dropdown filter (All, Locked, Unlocked)
  - Add date range inputs (from/to)
  - Add "Clear Filters" button
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3.2 Implement DataTables filtering
  - Enhance existing DataTables initialization in batch_list.html
  - Implement search functionality using DataTables search API
  - Implement dropdown filters using DataTables column filtering
  - Implement date range filtering with custom filter function
  - Update table without page reload
  - _Requirements: 2.5, 8.1_

- [x] 3.3 Enhance batch table visual design
  - Make order count numbers larger and more prominent (use fs-4 or fs-3)
  - Add carrier summary badges in table rows (show top 2-3 carriers)
  - Improve locked/unlocked status badge styling
  - Ensure responsive column hiding for mobile (hide less important columns on small screens)
  - _Requirements: 3.1, 3.2, 3.3, 6.2_

- [ ] 4. Batch Create Page Improvements
  - Enhance the batch creation flow with better preview and UX
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4.1 Enhance preview section visual design
  - Redesign preview cards in `templates/batch_create.html` with larger, more prominent numbers
  - Add visual carrier distribution (use Bootstrap progress bars or colored cards)
  - Improve shop distribution table with better styling and sorting
  - Make platform badge and run info more prominent at top
  - _Requirements: 4.1, 4.2, 3.1, 3.2_

- [ ] 4.2 Improve run number selector UX
  - Change dropdown to radio buttons for better visibility
  - Highlight suggested next run number (add badge or different styling)
  - Optionally show existing batches for the selected date below selector
  - Ensure Batch ID preview updates in real-time (existing JavaScript already does this)
  - _Requirements: 4.2, 4.5_

- [ ] 4.3 Enhance navigation and user feedback
  - Make "Back" button more prominent (larger size, better positioning)
  - Ensure warning about batch locking is clearly visible (use alert-warning)
  - Add client-side confirmation dialog before creating batch
  - Show loading indicator during batch creation (disable button, show spinner)
  - Improve success message display (already redirects, ensure flash message is clear)
  - _Requirements: 4.3, 4.4, 4.5, 7.5_

- [x] 5. Batch Detail Page Enhancements
  - Improve batch detail page with better visualizations and data display
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.1 Enhance summary cards visual design
  - Make numbers in existing KPI cards larger (use display-3 or display-4 classes)
  - Improve card styling with better colors and spacing
  - Add emoji icons to cards for visual appeal
  - Ensure responsive layout (cards stack on mobile)
  - _Requirements: 5.1, 3.1, 3.2, 6.1_

- [x] 5.2 Improve carrier summary visualization
  - Enhance existing carrier summary section with better visual design
  - Use larger numbers and color-coded badges
  - Consider adding simple progress bars or percentage indicators
  - Sort carriers by count (descending)
  - _Requirements: 5.2, 3.1, 3.3_

- [x] 5.3 Improve shop summary visualization
  - Enhance existing shop summary cards layout
  - Sort shops by count (descending) - add sorting logic
  - Make top shops more prominent (larger cards or badges)
  - Improve responsive layout for mobile
  - _Requirements: 5.3, 3.3_

- [x] 5.4 Enhance orders table functionality
  - Increase DataTables page length to 50 (currently 50, keep as is)
  - Ensure search functionality works well
  - Add column visibility toggle for less important columns
  - Improve responsive design (hide columns on mobile)
  - _Requirements: 5.4, 6.2, 8.1_

- [x] 5.5 Add Excel export functionality
  - Add "Export to Excel" button to batch detail page
  - Implement backend route `/batch/<batch_id>/export.xlsx`
  - Export all orders in batch with key fields (order_id, sku, qty, carrier, shop)
  - Style export button consistently with existing JSON button
  - _Requirements: 5.5_

- [ ] 6. Responsive Design Testing and Fixes
  - Test all batch pages on mobile and fix any layout issues
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 6.1 Test and fix Batch List responsive design
  - Test page on mobile viewport (< 576px) using browser dev tools
  - Ensure pending orders cards stack vertically
  - Make Quick Create buttons touch-friendly (min 44px height)
  - Test Quick Create modal on mobile (ensure it fits screen)
  - Fix any layout issues with filters or table
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 6.2 Test and fix Batch Create responsive design
  - Test page on mobile viewport
  - Ensure platform selection cards stack vertically
  - Test radio buttons are touch-friendly
  - Ensure preview cards display correctly and stack on mobile
  - Fix any layout issues with form elements
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 6.3 Test and fix Batch Detail responsive design
  - Test page on mobile viewport
  - Ensure summary cards stack properly (use col-md-* classes)
  - Test DataTables responsive mode (columns should hide on mobile)
  - Ensure all buttons are accessible and touch-friendly
  - Fix any layout issues with carrier/shop summaries
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 7. Error Handling and User Feedback
  - Improve error messages and user feedback for Quick Create and other features
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7.1 Implement error handling in new API endpoints
  - Add try-catch blocks in `/batch/next-run/<platform>` and `/batch/quick-create/<platform>`
  - Return consistent JSON error response format: `{success: false, error: "code", message: "Thai message"}`
  - Log errors to console or audit log for debugging
  - Provide user-friendly error messages in Thai
  - _Requirements: 7.1, 7.2_

- [ ] 7.2 Implement error display in Quick Create modal
  - Create JavaScript function to display errors in modal
  - Show Bootstrap alerts for errors (alert-danger)
  - Make error messages dismissible
  - Clear previous errors before new requests
  - _Requirements: 7.1, 7.5_

- [ ] 7.3 Add loading states to Quick Create
  - Show loading spinner in modal while fetching preview data
  - Disable confirm button and show spinner during batch creation
  - Prevent duplicate submissions (disable button after click)
  - Re-enable button if error occurs
  - _Requirements: 7.3, 7.4_

- [x] 8. Performance Optimization
  - Optimize database queries and page load times
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8.1 Add database indexes for batch queries
  - Add index on (Batch.platform, Batch.batch_date) in models.py or migration script
  - Add index on Batch.created_at for sorting
  - Verify existing indexes on OrderLine.batch_status and OrderLine.batch_id
  - Test query performance with EXPLAIN (optional)
  - _Requirements: 8.1, 8.5_

- [x] 8.2 Optimize batch list query
  - Review batch_list route query performance
  - Consider adding eager loading for relationships if needed
  - Ensure pending orders count query is efficient
  - Test with large number of batches (100+)
  - _Requirements: 8.1, 8.5_

- [x] 8.3 Test page load performance
  - Test Batch List page load time (target < 2 seconds)
  - Test Quick Create modal data fetch (target < 1 second)
  - Test batch creation time (target < 3 seconds)
  - Identify and fix any slow operations
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 9. Testing and Quality Assurance
  - Test all new functionality and fix any bugs
  - _Requirements: All_

- [ ] 9.1 Test Quick Create flow end-to-end
  - Test Quick Create for each platform (Shopee, Lazada, TikTok)
  - Test with no pending orders (should show error or disable button)
  - Test with pending orders (should show preview and create batch)
  - Test error scenarios (invalid platform, network error)
  - Verify batch is created correctly in database with correct run number
  - Verify audit log entry is created
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 9.2 Test Batch List filtering and search
  - Test search by Batch ID
  - Test platform filter (All, Shopee, Lazada, TikTok)
  - Test status filter (All, Locked, Unlocked)
  - Test date range filter
  - Test clear filters button
  - Test table sorting by different columns
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3_

- [x] 9.3 Test Batch Create page improvements
  - Test platform selection flow
  - Test run number selector (radio buttons)
  - Test Batch ID preview updates correctly
  - Test batch creation with confirmation
  - Test error handling (duplicate batch, no orders)
  - Test on mobile viewport
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 9.4 Test Batch Detail page enhancements
  - Test summary cards display correctly
  - Test carrier summary visualization
  - Test shop summary visualization and sorting
  - Test orders table search and pagination
  - Test Excel export functionality
  - Test on mobile viewport
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 9.5 Cross-browser and responsive testing
  - Test on Chrome (latest)
  - Test on Firefox (latest)
  - Test on Safari (if available)
  - Test on mobile devices (iOS/Android) or browser dev tools
  - Fix any browser-specific or responsive issues
  - _Requirements: All_

- [ ] 10. Documentation
  - Document new features and changes
  - _Requirements: All_

- [ ] 10.1 Add code documentation
  - Add docstrings to new helper functions (get_next_run_number)
  - Add comments for new API endpoints
  - Document Quick Create modal JavaScript functions
  - Add inline comments for complex logic
  - _Requirements: All_

- [ ] 10.2 Update user-facing documentation
  - Document Quick Create feature usage (how to use ⚡ button)
  - Document new filtering capabilities on Batch List
  - Document Excel export feature on Batch Detail
  - Update README.md or create BATCH_MANAGEMENT.md guide
  - _Requirements: All_
