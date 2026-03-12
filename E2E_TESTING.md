# AI-Powered Personalized Marketing - End-to-End Testing Guide

## Overview
This guide provides comprehensive end-to-end testing scenarios for the AI-powered personalized marketing platform. The app processes customer order data from CSV files, builds preference profiles, and generates personalized marketing campaigns.

## Prerequisites
- Backend server running (typically on `http://localhost:8000`)
- Frontend application running (typically on `http://localhost:3000`)
- PostgreSQL database connected and migrated
- OpenRouter API key configured for AI features
- Qdrant vector store running for semantic search

## Test Data Files

### Demo CSV: `demo_orders.csv`
Use the provided `demo_orders.csv` file for realistic testing data.

### Additional Test Files (Optional)
- `invalid_data.csv` - Contains validation errors
- `large_dataset.csv` - Performance testing with 1000+ orders
- `edge_cases.csv` - Special characters, nulls, edge cases

---

## 🚀 Test Scenario 1: Complete Workflow - Data Import to Campaign

### Step 1: Data Upload & Validation
1. Navigate to **Data Import** page
2. Upload `demo_orders.csv` using drag-and-drop
3. Review validation results:
   - ✅ Check for successful validation
   - ✅ Verify row count matches expectations
   - ✅ Confirm no critical errors
4. Click **Import Data** to proceed
5. Monitor processing progress:
   - ✅ Status updates from "processing" to "completed"
   - ✅ Success message with import summary

### Step 2: Customer Data Verification
1. Navigate to **Customers** page
2. Verify customer records:
   - ✅ Correct number of customers created
   - ✅ Customer profiles populated with names, emails
   - ✅ Order statistics calculated correctly
3. Click on a customer to view detailed profile:
   - ✅ Order history displayed
   - ✅ Preference profile generated
   - ✅ Favorite items and cuisines identified

### Step 3: Campaign Creation
1. Navigate to **Campaigns** page
2. Create new campaign:
   - Campaign Name: "Test Weekend Promotion"
   - Campaign Purpose: "Increase weekend orders"
3. Set segment filters:
   - Minimum orders: 2
   - Minimum spend: $50
   - Include vegetarian preferences
4. Click **Preview Audience**:
   - ✅ Verify audience count matches filters
   - ✅ Segment criteria displayed
5. Generate sample message:
   - ✅ Personalized content created
   - ✅ Customer preferences reflected
6. Execute campaign:
   - ✅ Campaign status updates
   - ✅ Messages generated for all segment customers

---

## 🔍 Test Scenario 2: Data Validation & Error Handling

### Invalid Email Formats
1. Create CSV with invalid emails: `invalid_emails.csv`
2. Upload and verify:
   - ❌ Validation errors detected
   - ✅ Specific error messages for email format
   - ✅ Rows with errors highlighted

### Negative Quantities & Prices
1. Create CSV with negative values
2. Verify:
   - ❌ Validation prevents import
   - ✅ Clear error messages for quantity/price validation

### Missing Required Fields
1. Create CSV with missing required columns
2. Verify:
   - ❌ Upload rejected
   - ✅ Missing fields clearly identified

### Large File Upload
1. Upload large dataset (>1000 orders)
2. Verify:
   - ✅ Progress indicators work
   - ✅ Processing completes within reasonable time
   - ✅ Memory usage stays within limits

---

## 🧠 Test Scenario 3: AI Features & Personalization

### Preference Profile Generation
1. Select a customer with multiple orders
2. Verify preference profile:
   - ✅ Favorite cuisines identified correctly
   - ✅ Dietary preferences detected (vegetarian, etc.)
   - ✅ Price sensitivity calculated
   - ✅ Order frequency patterns analyzed

### Personalized Message Generation
1. Create campaign with sample customer
2. Generate personalized message:
   - ✅ Message references customer's favorite items
   - ✅ Tone appropriate for customer's preferences
   - ✅ Personalization elements (name, favorite dishes)

### Menu Item Recommendations
1. View customer recommendations
2. Verify:
   - ✅ Recommendations based on order history
   - ✅ New items similar to preferences
   - ✅ Dietary restrictions respected

---

## 📊 Test Scenario 4: Data Analytics & Reporting

### Customer Analytics
1. Navigate to customer analytics
2. Verify:
   - ✅ Total customers count
   - ✅ Average order value
   - ✅ Most popular items
   - ✅ Revenue by time period

### Campaign Performance
1. View completed campaigns
2. Verify:
   - ✅ Campaign metrics displayed
   - ✅ Message delivery status
   - ✅ Customer engagement data

### Order Trend Analysis
1. Check order trends
2. Verify:
   - ✅ Peak ordering times identified
   - ✅ Popular categories displayed
   - ✅ Customer retention metrics

---

## 🔒 Test Scenario 5: Security & Permissions

### Data Access Control
1. Verify sensitive data protection:
   - ✅ Passwords/PII not exposed in logs
   - ✅ Customer data properly secured
   - ✅ API endpoints properly authenticated

### Input Validation
1. Test various injection attempts:
   - ✅ SQL injection protection
   - ✅ XSS prevention in user inputs
   - ✅ File upload restrictions

---

## ⚡ Test Scenario 6: Performance & Load Testing

### API Response Times
1. Test key endpoints:
   - Customer listing: <500ms
   - Order data: <1s for 1000 records
   - Campaign generation: <30s for 100 customers

### Concurrent Users
1. Simulate multiple users:
   - ✅ CSV uploads from multiple users
   - ✅ Campaign generation concurrency
   - ✅ Database connection pooling

### Database Performance
1. Monitor database queries:
   - ✅ Efficient indexing usage
   - ✅ Query optimization working
   - ✅ Connection limits respected

---

## 🔧 Test Scenario 7: Browser & Device Compatibility

### Cross-Browser Testing
Test in:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

### Responsive Design
Test on:
- ✅ Desktop (1920x1080)
- ✅ Tablet (768x1024)
- ✅ Mobile (375x667)

---

## 📝 Test Scenario 8: Data Integrity & Consistency

### Database Transactions
1. Test rollback scenarios:
   - ✅ Partial import failures rolled back
   - ✅ Campaign generation errors handled
   - ✅ Concurrent access consistency

### Data Relationships
1. Verify referential integrity:
   - ✅ Orders link to valid customers
   - ✅ Campaigns reference existing segments
   - ✅ Cascade deletes work correctly

---

## 🚨 Critical Error Scenarios

### Database Connection Loss
1. Stop database during operation
2. Verify:
   - ✅ Graceful error handling
   - ✅ User-friendly error messages
   - ✅ Recovery mechanisms

### API Service Unavailability
1. Simulate OpenRouter API outage
2. Verify:
   - ✅ Campaign creation handles API failure
   - ✅ Retry mechanisms work
   - ✅ Fallback behavior defined

### File System Errors
1. Test with invalid file permissions
2. Verify:
   - ✅ Upload errors handled gracefully
   - ✅ Temporary files cleaned up
   - ✅ Disk space monitoring

---

## 📋 Validation Checklist

### ✅ Data Import
- [ ] CSV upload works with valid data
- [ ] Validation catches all error types
- [ ] Large files process successfully
- [ ] Progress indicators accurate
- [ ] Error messages helpful and specific

### ✅ Customer Management
- [ ] Customer profiles complete
- [ ] Preference profiles accurate
- [ ] Order history correct
- [ ] Search and filter work

### ✅ Campaign Features
- [ ] Segmentation logic correct
- [ ] Personalized messages generated
- [ ] Campaign execution successful
- [ ] Performance metrics tracked

### ✅ UI/UX
- [ ] Responsive design works
- [ ] Loading states appropriate
- [ ] Error states handled
- [ ] Navigation intuitive

### ✅ Performance
- [ ] Response times within limits
- [ ] Memory usage reasonable
- [ ] Database queries optimized
- [ ] Concurrency handled

---

## 🔍 Debugging & Troubleshooting

### Common Issues

**CSV Import Fails**
- Check file format (UTF-8 encoding)
- Verify required columns present
- Validate date formats
- Check for special characters

**Campaign Generation Slow**
- Verify OpenRouter API key
- Check vector store connectivity
- Monitor database performance
- Review segment size

**Customer Preferences Missing**
- Ensure sufficient order history
- Check vector embeddings generation
- Verify AI model availability

### Log Locations
- Backend logs: Console output or log files
- Frontend logs: Browser developer tools
- Database logs: PostgreSQL log files
- Vector store logs: Qdrant logs

---

## 📞 Support Information

### Technical Contact
- Backend issues: Check API logs and database connectivity
- Frontend issues: Check browser console and network requests
- AI features: Verify OpenRouter API status and credits

### Environment Variables
Ensure these are properly configured:
- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `QDRANT_URL`
- `FRONTEND_URL`

---

## 🎯 Success Metrics

A successful end-to-end test should demonstrate:
- ✅ Complete workflow execution without errors
- ✅ Data integrity maintained throughout
- ✅ Personalization features working accurately
- ✅ Performance within acceptable limits
- ✅ Error handling robust and user-friendly
- ✅ Security measures properly implemented

---

*Last Updated: 2025-02-11*
*Version: 1.0*