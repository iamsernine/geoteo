# 🐛 AirWatch - Issues & Fixes Tracker

## Status Legend
- 🔴 **Critical** - Must fix immediately
- 🟠 **High** - Should fix soon
- 🟡 **Medium** - Nice to have
- 🟢 **Low** - Enhancement

---

## 🔴 Critical Issues

### [ISSUE-001] Missing Search Functionality
**Status**: 🔴 Critical  
**Location**: `app.py:247-259, 850-857`  
**Description**: Search modal opens but has no callback to actually search locations  
**Impact**: Broken feature, poor UX  
**Fix**: Add search callback to filter locations by name/country

### [ISSUE-002] Map Click Handler Missing
**Status**: 🔴 Critical  
**Location**: Map callbacks  
**Description**: No callback to handle map clicks, can't select locations or add to favorites from map  
**Impact**: Limited interactivity, `selected-location` store never updated  
**Fix**: Add click event handler to map, update selected location store

### [ISSUE-003] Weather Data Shows Wrong Location
**Status**: 🔴 Critical  
**Location**: `app.py:602-643`  
**Description**: Weather always shows for first location in data, not selected location  
**Impact**: Confusing UX, inaccurate data  
**Fix**: Use selected location or user's location for weather display

---

## 🟠 High Priority Issues

### [ISSUE-004] Incomplete Analytics Features
**Status**: 🟠 High  
**Location**: `app.py:701-711`  
**Description**: "Trends" and "Compare" tabs show placeholder messages  
**Impact**: Misleading UI, incomplete features  
**Fix**: Implement actual trend analysis and comparison functionality

### [ISSUE-005] No Loading States
**Status**: 🟠 High  
**Location**: Multiple callbacks  
**Description**: No loading indicators during API calls except for map  
**Impact**: Poor UX during slow operations  
**Fix**: Add loading indicators to all data-fetching operations

### [ISSUE-006] Database Connection Management
**Status**: 🟠 High  
**Location**: `backend/database.py`  
**Description**: Creates new connection for each operation, no connection pooling  
**Impact**: Could lead to connection exhaustion  
**Fix**: Implement connection pooling or context managers

### [ISSUE-007] No Error Feedback to Users
**Status**: 🟠 High  
**Location**: All callbacks  
**Description**: Errors logged but users don't see feedback  
**Impact**: Users don't know when operations fail  
**Fix**: Add toast notifications for errors/success

---

## 🟡 Medium Priority Issues

### [ISSUE-008] Missing Empty States
**Status**: 🟡 Medium  
**Location**: Favorites, History, Search views  
**Description**: No empty state messages when no data  
**Impact**: Confusing UX  
**Fix**: Add helpful empty state messages

### [ISSUE-009] No Input Validation
**Status**: 🟡 Medium  
**Location**: Search, Settings inputs  
**Description**: No validation of user inputs  
**Impact**: Could cause errors or security issues  
**Fix**: Add input validation and sanitization

### [ISSUE-010] API Rate Limiting Missing
**Status**: 🟡 Medium  
**Location**: `backend/api_client.py`  
**Description**: No rate limiting protection, could hit API limits  
**Impact**: Service disruption  
**Fix**: Implement rate limiting and retry logic

### [ISSUE-011] No Data Freshness Indicator
**Status**: 🟡 Medium  
**Location**: Main view  
**Description**: No indication of when data was last updated  
**Impact**: Users don't know if data is stale  
**Fix**: Add "Last updated" timestamp

---

## 🟢 Low Priority / Enhancements

### [ISSUE-012] Missing Accessibility Features
**Status**: 🟢 Low  
**Description**: Missing ARIA labels, keyboard navigation  
**Fix**: Add accessibility attributes

### [ISSUE-013] Mobile Responsiveness
**Status**: 🟢 Low  
**Description**: Sidebar might not work well on mobile  
**Fix**: Improve mobile layout

### [ISSUE-014] No Historical Data Visualization
**Status**: 🟢 Low  
**Description**: Trends tab placeholder  
**Fix**: Implement time series charts

### [ISSUE-015] Missing Tests
**Status**: 🟢 Low  
**Description**: No unit or integration tests  
**Fix**: Add pytest test suite

---

## Fix Progress

- [x] ISSUE-001: Missing Search Functionality ✅
- [x] ISSUE-002: Map Click Handler Missing ✅
- [x] ISSUE-003: Weather Data Shows Wrong Location ✅
- [x] ISSUE-002-BUG: Map error "location_id not in index" ✅
- [ ] ISSUE-004: Incomplete Analytics Features
- [ ] ISSUE-005: No Loading States
- [ ] ISSUE-006: Database Connection Management
- [ ] ISSUE-007: No Error Feedback to Users
- [ ] ISSUE-008: Missing Empty States
- [ ] ISSUE-009: No Input Validation
- [ ] ISSUE-010: API Rate Limiting Missing
- [ ] ISSUE-011: No Data Freshness Indicator

---

*Last Updated: 2026-01-07*

