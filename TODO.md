# NeoWX Material - Refactoring TODO

## Overview
This TODO file provides a detailed implementation plan for the refactoring opportunities identified in `explainme.md`. Each item includes specific actions, estimated effort, and implementation order.

## Priority Classification
- 🔴 **High Priority** - Critical improvements for maintainability and development experience
- 🟡 **Medium Priority** - Important enhancements that improve project quality
- 🟢 **Low Priority** - Nice-to-have improvements for polish and optimization

---

## 🔴 HIGH PRIORITY REFACTORING

### 1. Template Modularization
**Goal**: Reduce code duplication and improve template maintainability

#### 1.1 Extract Repeated Template Patterns
- [ ] **Audit template files for repeated patterns** (Est: 2 hours)
  - [ ] Analyze `index.html.tmpl`, `history.html.tmpl`, `year.html.tmpl`, etc.
  - [ ] Identify common card components, chart containers, and layout patterns
  - [ ] Document repeated code blocks with line numbers and usage frequency

- [ ] **Create reusable template macros** (Est: 8 hours)
  - [ ] Create `macros/cards.inc` for weather data cards
    - [ ] Extract `valuesCard` macro from index.html.tmpl
    - [ ] Create `chartCard` macro for chart containers
    - [ ] Create `statsCard` macro for statistical displays
  - [ ] Create `macros/charts.inc` for chart components
    - [ ] Extract chart initialization patterns
    - [ ] Create configurable chart wrapper macro
  - [ ] Create `macros/navigation.inc` for nav components
    - [ ] Extract breadcrumb patterns
    - [ ] Create consistent navigation macro

- [ ] **Update all template files to use macros** (Est: 6 hours)
  - [ ] Replace repeated patterns in `index.html.tmpl`
  - [ ] Replace repeated patterns in `history.html.tmpl`
  - [ ] Replace repeated patterns in `year.html.tmpl`
  - [ ] Replace repeated patterns in `month.html.tmpl`
  - [ ] Replace repeated patterns in `week.html.tmpl`
  - [ ] Replace repeated patterns in `yesterday.html.tmpl`
  - [ ] Replace repeated patterns in `almanac.html.tmpl`
  - [ ] Replace repeated patterns in `archive.html.tmpl`

#### 1.2 Consolidate Chart Configuration Files
- [ ] **Analyze chart configuration duplication** (Est: 1 hour)
  - [ ] Compare `graph_line_config.inc` vs `graph_line_archive_config.inc`
  - [ ] Compare `graph_area_config.inc` vs `graph_area_archive_config.inc`
  - [ ] Compare `graph_bar_config.inc` vs `graph_bar_archive_config.inc`
  - [ ] Document differences and commonalities

- [ ] **Create unified chart configuration system** (Est: 4 hours)
  - [ ] Create `chart_configs/base_config.inc` with common settings
  - [ ] Create `chart_configs/chart_factory.inc` with conditional logic
  - [ ] Add parameters for archive vs current data mode
  - [ ] Implement responsive chart sizing logic

- [ ] **Migrate existing chart configurations** (Est: 3 hours)
  - [ ] Update all templates to use new unified system
  - [ ] Remove deprecated individual config files
  - [ ] Test chart rendering on all pages

### 2. JavaScript Organization & Modernization
**Goal**: Implement modern JavaScript architecture for better maintainability

#### 2.1 Implement ES6 Module System
- [ ] **Setup modern JavaScript build pipeline** (Est: 4 hours)
  - [ ] Install and configure Webpack or Rollup
  - [ ] Configure Babel for ES6+ transpilation
  - [ ] Setup source maps for debugging
  - [ ] Configure development vs production builds

- [ ] **Restructure existing JavaScript** (Est: 6 hours)
  - [ ] Create `js/modules/` directory structure:
    - [ ] `js/modules/charts.js` - Chart initialization and management
    - [ ] `js/modules/tooltips.js` - Tooltip functionality
    - [ ] `js/modules/utils.js` - Utility functions (formatNumber, etc.)
    - [ ] `js/modules/theme.js` - Theme switching and dark mode
    - [ ] `js/modules/pwa.js` - Progressive Web App features
  - [ ] Create `js/app.js` as main entry point
  - [ ] Implement proper module imports/exports

- [ ] **Add error handling and logging** (Est: 2 hours)
  - [ ] Implement try-catch blocks for all major functions
  - [ ] Add console logging for debugging
  - [ ] Create error reporting mechanism

#### 2.2 TypeScript Migration (Optional)
- [ ] **Setup TypeScript environment** (Est: 3 hours)
  - [ ] Install TypeScript and type definitions
  - [ ] Configure tsconfig.json
  - [ ] Setup build pipeline integration

- [ ] **Migrate JavaScript modules to TypeScript** (Est: 8 hours)
  - [ ] Add type definitions for WeeWX data structures
  - [ ] Add type definitions for chart configurations
  - [ ] Migrate utility functions with proper typing
  - [ ] Add interface definitions for configuration objects

### 3. CSS Architecture Improvements
**Goal**: Implement modern CSS architecture with better theming support

#### 3.1 Implement CSS Custom Properties
- [ ] **Create design token system** (Est: 4 hours)
  - [ ] Create `scss/_design-tokens.scss` with CSS custom properties
  - [ ] Define color palette as CSS custom properties
  - [ ] Define spacing scale as CSS custom properties
  - [ ] Define typography scale as CSS custom properties
  - [ ] Define breakpoints as CSS custom properties

- [ ] **Update existing SCSS to use design tokens** (Est: 6 hours)
  - [ ] Replace hardcoded colors with CSS custom properties
  - [ ] Replace hardcoded spacing with scale variables
  - [ ] Update `_custom-variables.scss` to use design tokens
  - [ ] Update Material Design color mappings

#### 3.2 Optimize SCSS Architecture
- [ ] **Restructure SCSS imports** (Est: 2 hours)
  - [ ] Analyze current import dependencies
  - [ ] Optimize import order for faster compilation
  - [ ] Remove unused Bootstrap components
  - [ ] Create partial imports for better tree-shaking

- [ ] **Implement BEM methodology** (Est: 8 hours)
  - [ ] Audit existing CSS classes for naming consistency
  - [ ] Rename classes to follow BEM convention
  - [ ] Update all template files with new class names
  - [ ] Create SCSS mixins for common BEM patterns

### 4. Configuration Management Enhancement
**Goal**: Improve configuration system reliability and user experience

#### 4.1 Implement Configuration Validation
- [ ] **Create configuration schema** (Est: 3 hours)
  - [ ] Define JSON schema for `skin.conf` structure
  - [ ] Define validation rules for color themes
  - [ ] Define validation rules for chart configurations
  - [ ] Define validation rules for language settings

- [ ] **Implement validation script** (Est: 4 hours)
  - [ ] Create `bin/validate_config.py` script
  - [ ] Add validation to patch application script
  - [ ] Add user-friendly error messages
  - [ ] Create configuration repair suggestions

#### 4.2 Enhance Patch System
- [ ] **Improve patch script robustness** (Est: 3 hours)
  - [ ] Add validation for patch file syntax
  - [ ] Implement atomic patch application (rollback on failure)
  - [ ] Add patch versioning support
  - [ ] Create patch conflict detection

- [ ] **Add configuration management tools** (Est: 4 hours)
  - [ ] Create `bin/config_manager.py` utility
  - [ ] Add commands: validate, backup, restore, merge
  - [ ] Add interactive configuration wizard
  - [ ] Create configuration diff tool

---

## 🟡 MEDIUM PRIORITY REFACTORING

### 5. Build System Modernization
**Goal**: Improve development experience and build performance

#### 5.1 Replace Current Build System
- [ ] **Evaluate build tool options** (Est: 2 hours)
  - [ ] Compare Vite vs Webpack vs Rollup for this project
  - [ ] Evaluate npm vs yarn vs pnpm for package management
  - [ ] Document pros/cons for each option

- [ ] **Implement new build system** (Est: 6 hours)
  - [ ] Setup chosen build tool configuration
  - [ ] Migrate from yarn to chosen package manager
  - [ ] Configure development server with hot reload
  - [ ] Setup production build optimization
  - [ ] Configure asset bundling and minification

- [ ] **Create development workflow** (Est: 3 hours)
  - [ ] Setup watch mode for SCSS compilation
  - [ ] Configure browser sync for live reload
  - [ ] Add build scripts for different environments
  - [ ] Create deployment preparation scripts

#### 5.2 Asset Optimization Pipeline
- [ ] **Implement image optimization** (Est: 2 hours)
  - [ ] Setup imagemin or similar tool
  - [ ] Optimize existing PNG/ICO files
  - [ ] Generate WebP versions for modern browsers
  - [ ] Implement responsive image generation

- [ ] **JavaScript bundling optimization** (Est: 3 hours)
  - [ ] Implement code splitting for vendor libraries
  - [ ] Setup tree shaking for unused code elimination
  - [ ] Configure dynamic imports for chart libraries
  - [ ] Implement bundle analysis tools

### 6. Testing Infrastructure Implementation
**Goal**: Ensure code quality and prevent regressions

#### 6.1 Unit Testing Setup
- [ ] **Setup JavaScript testing framework** (Est: 3 hours)
  - [ ] Choose testing framework (Jest, Vitest, or similar)
  - [ ] Configure test environment for browser APIs
  - [ ] Setup test utilities and mocks
  - [ ] Configure coverage reporting

- [ ] **Write JavaScript unit tests** (Est: 8 hours)
  - [ ] Test utility functions (formatNumber, etc.)
  - [ ] Test chart configuration generation
  - [ ] Test theme switching functionality
  - [ ] Test tooltip initialization
  - [ ] Test PWA feature detection

#### 6.2 Template Testing
- [ ] **Setup template testing environment** (Est: 4 hours)
  - [ ] Research Cheetah template testing approaches
  - [ ] Setup mock WeeWX data for testing
  - [ ] Create template rendering test utilities
  - [ ] Configure test data fixtures

- [ ] **Write template tests** (Est: 6 hours)
  - [ ] Test macro functionality
  - [ ] Test conditional rendering logic
  - [ ] Test data binding and formatting
  - [ ] Test internationalization functionality

#### 6.3 Configuration Testing
- [ ] **Test configuration system** (Est: 4 hours)
  - [ ] Test patch application and rollback
  - [ ] Test configuration validation
  - [ ] Test configuration migration
  - [ ] Test error handling and recovery

### 7. Documentation System Enhancement
**Goal**: Improve developer onboarding and maintenance

#### 7.1 API Documentation
- [ ] **Document template functions** (Est: 4 hours)
  - [ ] Create JSDoc-style comments for JavaScript functions
  - [ ] Document Cheetah template macros and functions
  - [ ] Document chart configuration options
  - [ ] Create API reference documentation

- [ ] **Create development guides** (Est: 6 hours)
  - [ ] Write "Getting Started" guide for new developers
  - [ ] Create "Adding New Features" guide
  - [ ] Write "Theming Guide" for customization
  - [ ] Create "Translation Guide" for new languages

#### 7.2 User Documentation
- [ ] **Create user guides** (Est: 4 hours)
  - [ ] Write installation and setup guide
  - [ ] Create configuration reference documentation
  - [ ] Write troubleshooting guide
  - [ ] Create FAQ document

- [ ] **Setup documentation website** (Est: 3 hours)
  - [ ] Choose documentation platform (GitBook, Docusaurus, etc.)
  - [ ] Setup documentation build pipeline
  - [ ] Create documentation deployment process
  - [ ] Implement search functionality

---

## 🟢 LOW PRIORITY REFACTORING

### 8. Performance Optimization
**Goal**: Improve loading times and runtime performance

#### 8.1 Chart Performance
- [ ] **Implement lazy loading for charts** (Est: 4 hours)
  - [ ] Setup Intersection Observer for chart containers
  - [ ] Load chart libraries only when needed
  - [ ] Implement chart data streaming for large datasets
  - [ ] Add loading indicators for chart initialization

- [ ] **Optimize chart rendering** (Est: 3 hours)
  - [ ] Implement chart data caching
  - [ ] Add chart zoom/pan performance optimizations
  - [ ] Optimize chart animation performance
  - [ ] Implement chart data decimation for performance

#### 8.2 Asset Optimization
- [ ] **Implement service worker** (Est: 5 hours)
  - [ ] Create service worker for offline functionality
  - [ ] Implement cache strategies for different asset types
  - [ ] Add background sync for data updates
  - [ ] Implement push notifications for weather alerts

- [ ] **Font optimization** (Est: 2 hours)
  - [ ] Implement font subsetting for Rubik font
  - [ ] Add font-display: swap for better performance
  - [ ] Preload critical font variants
  - [ ] Implement variable font if available

### 9. Accessibility Improvements
**Goal**: Ensure inclusive design and WCAG compliance

#### 9.1 ARIA Implementation
- [ ] **Add ARIA labels** (Est: 4 hours)
  - [ ] Add ARIA labels to interactive elements
  - [ ] Implement ARIA live regions for dynamic content
  - [ ] Add ARIA descriptions for chart elements
  - [ ] Implement ARIA navigation landmarks

- [ ] **Keyboard navigation** (Est: 3 hours)
  - [ ] Implement keyboard navigation for charts
  - [ ] Add focus management for modal dialogs
  - [ ] Implement skip links for main content
  - [ ] Add keyboard shortcuts for common actions

#### 9.2 Screen Reader Optimization
- [ ] **Content structure optimization** (Est: 3 hours)
  - [ ] Ensure proper heading hierarchy
  - [ ] Add descriptive text for charts and graphs
  - [ ] Implement table headers for data tables
  - [ ] Add alternative text for weather icons

### 10. Developer Experience Enhancement
**Goal**: Improve development workflow and tooling

#### 10.1 Development Environment
- [ ] **Setup live reload development server** (Est: 3 hours)
  - [ ] Configure development server with proxy to WeeWX
  - [ ] Implement hot module replacement
  - [ ] Add development-only debugging tools
  - [ ] Setup mock data for offline development

- [ ] **Code quality tools** (Est: 2 hours)
  - [ ] Setup ESLint with appropriate rules
  - [ ] Configure Prettier for code formatting
  - [ ] Setup Stylelint for SCSS linting
  - [ ] Add pre-commit hooks for quality checks

#### 10.2 IDE Configuration
- [ ] **VS Code workspace setup** (Est: 1 hour)
  - [ ] Create `.vscode/settings.json` with project settings
  - [ ] Add recommended extensions list
  - [ ] Configure debugging for JavaScript
  - [ ] Setup task runners for common operations

---

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-3)
Focus on high-priority infrastructure improvements:
1. Template modularization (1.1, 1.2)
2. Basic JavaScript organization (2.1)
3. CSS custom properties (3.1)
4. Configuration validation (4.1)

### Phase 2: Modernization (Weeks 4-6)
Implement modern development practices:
1. Complete JavaScript modernization (2.2)
2. Build system replacement (5.1)
3. Testing infrastructure (6.1, 6.2)
4. Documentation enhancement (7.1)

### Phase 3: Polish (Weeks 7-8)
Add performance and accessibility improvements:
1. Performance optimizations (8.1, 8.2)
2. Accessibility implementation (9.1, 9.2)
3. Developer experience tools (10.1, 10.2)

## Success Metrics

- **Code Quality**: Reduce code duplication by 60%, achieve 80%+ test coverage
- **Build Performance**: Reduce build time by 50%, implement <2s hot reload
- **Developer Experience**: New developer onboarding time reduced to <30 minutes
- **Accessibility**: Achieve WCAG 2.1 AA compliance
- **Performance**: Achieve Lighthouse score >90 for all pages

## Risk Mitigation

- **Backward Compatibility**: Maintain existing configuration compatibility throughout refactoring
- **Progressive Migration**: Implement changes incrementally to avoid breaking existing installations
- **Rollback Strategy**: Maintain ability to rollback each change independently
- **Testing Coverage**: Ensure comprehensive testing before deploying any breaking changes

---

**Last Updated**: August 27, 2025
**Next Review**: September 10, 2025
