# NeoWX Material - Refactoring Guide

## Project Overview

This is a fork of the NeoWX Material skin for WeeWX weather stations, maintained as the original repository is no longer active. The project provides a modern Material Design UI for weather station data with extensive customization options.

**Live Demo:** https://weewx.seehausen.org/

## Architecture Overview

### Core Components

1. **WeeWX Skin System** - Template-based weather station interface
2. **Material Design UI** - Modern responsive web interface
3. **Multi-language Support** - Internationalization system
4. **Chart/Graph System** - Interactive data visualization
5. **Configuration Management** - Flexible patch-based config system

## Directory Structure Analysis

```
neowx-material/
├── bin/user/                    # WeeWX extensions
│   └── historygenerator.py      # Custom data generator for historical tables
├── skins/neowx-material/        # Main skin directory
│   ├── *.html.tmpl              # Cheetah template files
│   ├── *.inc                    # Template includes
│   ├── skin.conf                # Main configuration
│   ├── skin_conf_patches.txt    # Custom configuration patches
│   ├── skin_conf_patch.sh       # Patch application script
│   ├── css/                     # Compiled stylesheets
│   ├── scss/                    # Source SCSS files
│   ├── js/                      # JavaScript files
│   ├── lang/                    # Language files
│   ├── img/                     # Icons and images
│   ├── fonts/                   # Custom fonts (Rubik)
│   └── weather-icons/           # Weather icon set
├── install.py                   # WeeWX extension installer
└── package.json                 # Node.js build configuration
```

## Key Technologies & Dependencies

### Frontend Stack
- **Bootstrap** - CSS framework for responsive design
- **Material Design Bootstrap (MDB)** - Material Design components
- **SCSS/Sass** - CSS preprocessing
- **jQuery** - JavaScript utilities
- **Cheetah Templates** - Server-side templating engine
- **Weather Icons** - Specialized weather iconography

### Build System
- **Node.js/Yarn** - Package management and build tools
- **Sass compiler** - CSS compilation pipeline

### Backend Integration
- **WeeWX** - Weather station software framework
- **Python extensions** - Custom data processing

## Configuration Architecture

### Multi-layered Configuration System

1. **Base Configuration** (`skin.conf`)
   - Default settings and theme configuration
   - Chart configurations
   - UI appearance settings

2. **Patch System** (`skin_conf_patches.txt` + `skin_conf_patch.sh`)
   - User customizations without merge conflicts
   - Section-aware key-value patching
   - Automatic backup creation

3. **Language Configuration** (`lang/*.conf`)
   - Internationalization support
   - Text translations and labels
   - Currently supports: ca, de, en, es, fi, fr, it, nl, pl, se, sk

## Template System

### Cheetah Template Structure
- **Main templates** - Full page layouts (`index.html.tmpl`, `history.html.tmpl`, etc.)
- **Include files** - Reusable components (`head.inc`, `header.inc`, `footer.inc`)
- **Configuration includes** - Chart and graph configurations
- **Archive templates** - Historical data presentation

### Template Features
- Server-side data binding with WeeWX
- Conditional rendering based on sensor availability
- Responsive design patterns
- SEO-friendly HTML structure

## Styling Architecture

### SCSS Organization
```
scss/
├── style.scss                   # Main entry point
├── _custom-variables.scss       # Theme customization
├── _neowx-material.scss         # Skin-specific styles
├── _rubik-font.scss            # Font definitions
├── core/                       # Bootstrap core files
└── free/                       # MDB free components
```

### Theme System
- **Color schemes** - 19 predefined Material Design color palettes
- **Dark mode support** - Automatic theme switching
- **Responsive breakpoints** - Mobile-first design
- **Custom CSS properties** - Theme-aware styling

## JavaScript Architecture

### Core Functionality
- **Tooltip support** - Enhanced UX with data tooltips
- **Number formatting** - WeeWX-compatible value formatting
- **Chart integration** - Interactive data visualization
- **Progressive Web App** - Manifest.json support

## Data Processing Pipeline

### Historical Data Generator (`historygenerator.py`)
- **Custom WeeWX extension** - Extends Cheetah search lists
- **Color-coded tables** - Temperature and rainfall visualization
- **Flexible time periods** - All-time, yearly, monthly statistics
- **Unit-aware formatting** - Respects skin.conf display settings

### Chart Configuration System
- **Multiple chart types** - Line, area, bar, and radar charts
- **Archive-specific configs** - Different settings for historical data
- **Responsive design** - Mobile-optimized chart rendering

## Internationalization System

### Language Support Architecture
- **Template-based translations** - WeeWX native i18n system
- **Modular language files** - Easy addition of new languages
- **Context-aware translations** - Weather-specific terminology
- **UTF-8 encoding** - Full Unicode support

## Installation & Extension System

### WeeWX Extension Format
- **StandardExtensionInstaller** - WeeWX-compatible installation
- **File manifest** - Complete file listing for installation
- **Configuration injection** - Automatic skin.conf integration

## Potential Refactoring Opportunities

### High Priority

1. **Template Modularization**
   - Extract repeated template patterns into reusable macros
   - Create component-based template architecture
   - Consolidate similar chart configuration files

2. **JavaScript Organization**
   - Implement ES6 modules for better code organization
   - Add TypeScript for better development experience
   - Create proper build pipeline for JS assets

3. **CSS Architecture**
   - Implement CSS custom properties for better theming
   - Optimize SCSS imports and reduce compilation time
   - Create design token system for consistent styling

4. **Configuration Management**
   - Implement JSON/YAML configuration format
   - Create configuration validation system
   - Add configuration migration scripts

### Medium Priority

5. **Build System Modernization**
   - Replace Yarn with npm or pnpm
   - Implement Webpack or Vite for asset bundling
   - Add development server with hot reload

6. **Testing Infrastructure**
   - Unit tests for JavaScript functionality
   - Template rendering tests
   - Configuration validation tests
   - Visual regression testing

7. **Documentation System**
   - API documentation for template functions
   - Configuration reference documentation
   - Development setup guide

### Low Priority

8. **Performance Optimization**
   - Implement lazy loading for charts
   - Optimize image assets and icons
   - Add service worker for offline functionality

9. **Accessibility Improvements**
   - ARIA labels for interactive elements
   - Keyboard navigation support
   - Screen reader optimization

10. **Developer Experience**
    - Live reload development environment
    - Linting and formatting configuration
    - VS Code extension recommendations

## Technology Migration Considerations

### Frontend Framework Migration
- **Consider:** React, Vue, or Alpine.js for component architecture
- **Benefits:** Better state management, component reusability
- **Challenges:** WeeWX template integration complexity

### Build Tool Modernization
- **Consider:** Vite, Rollup, or esbuild for faster builds
- **Benefits:** Improved development experience, better optimization
- **Implementation:** Gradual migration maintaining backward compatibility

### CSS Framework Updates
- **Consider:** Tailwind CSS or modern CSS features
- **Benefits:** Smaller bundle size, better customization
- **Challenges:** Material Design component replacement

## Development Workflow

### Current Setup
1. Edit SCSS files in `scss/` directory
2. Run `yarn build` to compile CSS
3. Modify templates and test with WeeWX
4. Apply configuration patches as needed

### Recommended Improvements
1. **Hot reload development server**
2. **Automated testing pipeline**
3. **Code formatting and linting**
4. **Git hooks for quality checks**

## Security Considerations

### Current Security Features
- No server-side code execution in templates
- Static file generation reduces attack surface
- Configuration file validation

### Areas for Improvement
- Content Security Policy implementation
- Input sanitization in configuration patches
- Secure default configurations

## Browser Compatibility

### Current Support
- Modern browsers with ES6 support
- Progressive Web App features
- Responsive design for mobile devices

### Legacy Support Considerations
- IE11 compatibility requires polyfills
- Graceful degradation for older browsers
- Feature detection for progressive enhancement

## Deployment Considerations

### Current Deployment
- Static file generation via WeeWX
- Manual installation via extension system
- Configuration through file editing

### Potential Improvements
- Docker containerization
- Automated deployment scripts
- Configuration management interface

---

**Note:** This refactoring guide should be updated as the project evolves. Regular reviews of this document will help maintain architectural consistency and guide future development decisions.
