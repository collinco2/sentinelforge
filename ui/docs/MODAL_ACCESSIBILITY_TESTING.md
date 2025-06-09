# 🔍 **Modal Accessibility Testing Guide**

## 📋 **Overview**

This document provides comprehensive testing procedures for modal dialog accessibility in the SentinelForge React UI. All modals have been enhanced with proper focus management, ESC-to-close behavior, and keyboard navigation support.

## 🎯 **Enhanced Modal Components**

### **✅ 1. UploadFeedModal**
- **Location**: `/feeds/upload`
- **Trigger**: "Upload Feed" button on Feed Management page
- **Features**: File upload, form validation, progress tracking

### **✅ 2. CreateApiKeyModal** 
- **Location**: `/settings` → API & Tokens tab
- **Trigger**: "Create Key" button in API Key Management
- **Features**: Multi-step form, validation, confirmation

### **✅ 3. Token Rotation Confirmation Dialog**
- **Location**: `/settings` → API & Tokens tab
- **Trigger**: "Rotate Token" button in Token Settings
- **Features**: Confirmation dialog with warning

### **✅ 4. API Key Revocation Dialog**
- **Location**: `/settings` → API & Tokens tab  
- **Trigger**: Revoke button on existing API keys
- **Features**: Destructive action confirmation

### **✅ 5. API Key Rotation Dialog**
- **Location**: `/settings` → API & Tokens tab
- **Trigger**: Rotate button on existing API keys
- **Features**: Key rotation confirmation

## 🧪 **Keyboard Navigation Test Procedures**

### **🔧 Test Setup**
1. **Disable Mouse**: Use browser dev tools or OS accessibility settings
2. **Screen Reader**: Test with NVDA, JAWS, or VoiceOver
3. **Browser**: Test in Chrome, Firefox, Safari, Edge
4. **Keyboard Only**: Navigate using only Tab, Shift+Tab, Enter, Space, ESC

---

## **📝 Test Case 1: UploadFeedModal**

### **🎯 Test Objective**
Verify complete keyboard accessibility for file upload workflow.

### **📋 Test Steps**

#### **Step 1: Modal Opening**
1. Navigate to `/feeds` page
2. Tab to "Upload Feed" button
3. Press `Enter` or `Space` to open modal
4. **✅ Verify**: Focus moves to first input field (Source Feed Name)
5. **✅ Verify**: Modal overlay traps focus within dialog

#### **Step 2: Form Navigation**
1. **Source Feed Input**: 
   - Type "Test Feed"
   - Press `Tab` to move to next field
2. **Justification Textarea**:
   - Type optional justification
   - Press `Tab` to move to file selection
3. **File Selection**:
   - Press `Enter` on "browse" link to open file picker
   - Select a test file (.csv, .json, .stix, .txt)

#### **Step 3: Advanced Settings**
1. Tab to "Advanced Settings" accordion
2. Press `Enter` to expand
3. Navigate through switches and sliders using `Tab`
4. Use `Space` to toggle switches
5. Use arrow keys to adjust sliders

#### **Step 4: Form Submission**
1. Tab to "Upload & Import" button
2. Press `Enter` to submit
3. **✅ Verify**: Upload progress is announced
4. **✅ Verify**: Success/error messages are accessible

#### **Step 5: Modal Closing**
1. **ESC Key**: Press `Escape` to close modal
2. **Cancel Button**: Tab to Cancel and press `Enter`
3. **✅ Verify**: Focus returns to trigger button

### **🎯 Expected Results**
- ✅ Focus management works correctly
- ✅ All form elements are keyboard accessible
- ✅ ESC key closes modal
- ✅ Screen reader announces all content
- ✅ Tab order is logical and complete

---

## **📝 Test Case 2: CreateApiKeyModal**

### **🎯 Test Objective**
Verify multi-step form accessibility and navigation.

### **📋 Test Steps**

#### **Step 1: Modal Opening**
1. Navigate to `/settings`
2. Click "API & Tokens" tab
3. Tab to "Create Key" button
4. Press `Enter` to open modal
5. **✅ Verify**: Focus moves to "Key Name" input

#### **Step 2: Step 1 - Basic Information**
1. **Key Name**: Type "Test API Key"
2. **Description**: Tab and type optional description
3. **Next Button**: Tab to "Next" and press `Enter`
4. **✅ Verify**: Step indicator updates

#### **Step 3: Step 2 - Access & Security**
1. **Permissions**: Use `Tab` and `Space` to select checkboxes
2. **Advanced Settings**: Tab to accordion, press `Enter` to expand
3. **Dropdowns**: Use arrow keys to select options
4. **Next Button**: Tab to "Next" and press `Enter`

#### **Step 4: Step 3 - Review & Create**
1. **Review Information**: Tab through read-only summary
2. **Previous Button**: Test going back with "Previous"
3. **Create Button**: Tab to "Create API Key" and press `Enter`
4. **✅ Verify**: Success message and new key display

#### **Step 5: Navigation Controls**
1. **Previous/Next**: Test step navigation
2. **Cancel**: Test canceling at any step
3. **ESC Key**: Test closing with Escape

### **🎯 Expected Results**
- ✅ Multi-step navigation works with keyboard
- ✅ Form validation provides accessible feedback
- ✅ Step indicators are properly announced
- ✅ All form controls are keyboard accessible

---

## **📝 Test Case 3: Confirmation Dialogs**

### **🎯 Test Objective**
Verify confirmation dialogs for destructive actions.

### **📋 Test Steps**

#### **Token Rotation Dialog**
1. Navigate to Token Settings
2. Tab to "Rotate Token" button
3. Press `Enter` to open confirmation
4. **✅ Verify**: Focus moves to dialog
5. **✅ Verify**: Warning content is announced
6. Tab between "Cancel" and "Rotate Token" buttons
7. Test both actions with `Enter`

#### **API Key Revocation Dialog**
1. Navigate to existing API key
2. Tab to "Revoke" button (red)
3. Press `Enter` to open confirmation
4. **✅ Verify**: Destructive action warning
5. Tab between "Cancel" and "Revoke Key" buttons
6. Test ESC to cancel

#### **API Key Rotation Dialog**
1. Navigate to existing API key
2. Tab to "Rotate" button
3. Press `Enter` to open confirmation
4. **✅ Verify**: Rotation explanation
5. Complete rotation workflow

### **🎯 Expected Results**
- ✅ Confirmation dialogs trap focus
- ✅ Warning content is clearly announced
- ✅ Button labels are descriptive
- ✅ ESC cancels destructive actions

---

## **🔍 Accessibility Checklist**

### **✅ Focus Management**
- [ ] Focus moves to first interactive element on open
- [ ] Focus is trapped within modal
- [ ] Focus returns to trigger element on close
- [ ] Tab order is logical and complete
- [ ] Focus indicators are visible

### **✅ Keyboard Navigation**
- [ ] All interactive elements are keyboard accessible
- [ ] ESC key closes modal
- [ ] Enter/Space activate buttons
- [ ] Arrow keys work for dropdowns/sliders
- [ ] Tab/Shift+Tab navigate correctly

### **✅ Screen Reader Support**
- [ ] Modal title is announced
- [ ] Form labels are associated correctly
- [ ] Error messages are announced
- [ ] Status updates are announced
- [ ] Button purposes are clear

### **✅ ARIA Implementation**
- [ ] `role="dialog"` on modal container
- [ ] `aria-labelledby` references title
- [ ] `aria-describedby` for descriptions
- [ ] `aria-live` for status updates
- [ ] `aria-expanded` for accordions

### **✅ Visual Design**
- [ ] Focus indicators meet contrast requirements
- [ ] Text meets WCAG 2.1 contrast standards
- [ ] Interactive elements are 44px minimum
- [ ] Color is not the only indicator

---

## **🚨 Common Issues to Test**

### **Focus Trapping**
- Tab from last element should return to first
- Shift+Tab from first element should go to last
- Focus should not escape modal

### **ESC Key Behavior**
- Should close modal without saving
- Should not close during critical operations
- Should return focus to trigger element

### **Form Validation**
- Error messages should be announced
- Invalid fields should receive focus
- Validation should not break navigation

### **Screen Reader Announcements**
- Modal opening should be announced
- Form submission status should be announced
- Error states should be clearly communicated

---

## **📊 Test Results Template**

```markdown
## Test Results: [Modal Name]
**Date**: [Date]
**Browser**: [Browser/Version]
**Screen Reader**: [SR/Version]
**Tester**: [Name]

### Focus Management
- [ ] ✅ PASS / ❌ FAIL - Focus moves to first element
- [ ] ✅ PASS / ❌ FAIL - Focus trapped in modal
- [ ] ✅ PASS / ❌ FAIL - Focus returns on close

### Keyboard Navigation  
- [ ] ✅ PASS / ❌ FAIL - All elements accessible
- [ ] ✅ PASS / ❌ FAIL - ESC closes modal
- [ ] ✅ PASS / ❌ FAIL - Tab order logical

### Screen Reader
- [ ] ✅ PASS / ❌ FAIL - Content announced
- [ ] ✅ PASS / ❌ FAIL - Labels associated
- [ ] ✅ PASS / ❌ FAIL - Status updates announced

**Issues Found**: [List any issues]
**Notes**: [Additional observations]
```

---

## **🔧 Automated Testing**

### **Cypress Tests**
```javascript
// Example test for modal accessibility
describe('Modal Accessibility', () => {
  it('should manage focus correctly', () => {
    cy.visit('/settings');
    cy.get('[data-testid="create-api-key-button"]').click();
    cy.focused().should('have.attr', 'data-testid', 'api-key-name-input');
    cy.get('body').type('{esc}');
    cy.focused().should('have.attr', 'data-testid', 'create-api-key-button');
  });
});
```

### **Jest + Testing Library**
```javascript
// Example unit test for keyboard navigation
test('modal closes on ESC key', () => {
  render(<UploadFeedModal isOpen={true} onClose={mockClose} />);
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(mockClose).toHaveBeenCalled();
});
```

---

**✨ All modal dialogs in SentinelForge now provide comprehensive accessibility support with proper focus management, keyboard navigation, and screen reader compatibility.**
