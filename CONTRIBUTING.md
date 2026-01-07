# Contributing to MindSpace

Thank you for your interest in contributing to MindSpace! 🎉 We're excited to have you as part of our team working on this intelligent framework for predicting student burnout. This guide will help you get started and make the contribution process smooth and enjoyable.

## Table of Contents

- [Reporting Issues](#reporting-issues)
- [Development Workflow](#development-workflow)
- [Coding Style Guidelines](#coding-style-guidelines)
- [Testing](#testing)
- [Code of Conduct](#code-of-conduct)
- [Questions?](#questions)

## Reporting Issues

We use GitHub Issues to track bugs, feature requests, and improvements. When reporting an issue:

### Bug Reports

If you've found a bug, please create an issue with the following information:

- **Clear title**: A brief, descriptive title
- **Description**: What happened vs. what you expected
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Environment**: OS, Python/Node version, relevant dependencies
- **Screenshots**: If applicable, add screenshots to illustrate the problem

### Feature Requests

Have an idea for a new feature? We'd love to hear it!

- **Use case**: Describe the problem you're trying to solve
- **Proposed solution**: How you think it should work
- **Alternatives**: Any alternative solutions you've considered

Feel free to discuss your ideas in issues before starting work on them. This helps ensure your efforts align with the project's direction and prevents duplicate work.

## Development Workflow

We follow a feature branch workflow to keep our codebase organized and make collaboration easier.

### 1. Create a Feature Branch

Start by creating a new branch from `main` for your work:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - for new features
- `bugfix/` - for bug fixes
- `docs/` - for documentation changes
- `refactor/` - for code refactoring

### 2. Make Your Changes

- Write clear, focused commits
- Commit messages should be descriptive (e.g., "Add sentiment analysis module" rather than "Update code")
- Keep commits atomic - each commit should represent a single logical change

### 3. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 4. Open a Pull Request

- Go to the repository on GitHub and create a Pull Request (PR)
- Fill out the PR template (if available) with:
  - **What**: What changes did you make?
  - **Why**: Why were these changes necessary?
  - **Testing**: How did you test your changes?
- Link any related issues using keywords like "Closes #123" or "Fixes #456"
- Request review from at least one team member

### 5. Address Review Feedback

- Respond to review comments promptly and professionally
- Make requested changes in new commits (avoid force-pushing during review)
- Mark conversations as resolved once addressed
- Re-request review after making significant changes

### 6. Merge

Once your PR is approved and all checks pass, it can be merged! We typically use "Squash and merge" to keep the commit history clean.

## Coding Style Guidelines

Consistent code style makes our codebase easier to read and maintain. Here are our general guidelines:

### General Principles

- **Readability first**: Code is read more often than it's written
- **Be consistent**: Follow the patterns you see in the existing codebase
- **Keep it simple**: Prefer clarity over cleverness
- **Document when necessary**: Add comments for complex logic, not obvious code

### Python Code (if applicable)

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Use type hints where appropriate

### JavaScript/TypeScript Code (if applicable)

- Use meaningful variable and function names
- Follow modern ES6+ conventions
- Add JSDoc comments for functions and complex logic
- Use `const` by default, `let` when reassignment is needed

### Documentation

- Update README.md if your changes affect setup or usage
- Keep comments up to date with code changes
- Document any new configuration options or environment variables

## Testing

Quality is important to us! Before submitting your PR:

### Before You Submit

1. **Run existing tests**: Make sure all tests pass
   ```bash
   # Python example
   pytest
   
   # Node.js example
   npm test
   ```

2. **Add new tests**: If you're adding new functionality, include tests that cover:
   - Happy path scenarios
   - Edge cases
   - Error conditions

3. **Test manually**: If applicable, test your changes manually to ensure they work as expected

4. **Check for errors**: Review your code for obvious issues like syntax errors, unused imports, or debug statements

### Writing Good Tests

- Tests should be clear and focused on one thing
- Use descriptive test names that explain what's being tested
- Ensure tests are repeatable and don't depend on external state
- Mock external dependencies when appropriate

## Code of Conduct

### Our Commitment

We're committed to providing a welcoming, friendly, and respectful environment for everyone on our team. We want MindSpace to be a project where everyone feels comfortable contributing and collaborating.

### Expected Behavior

- **Be respectful**: Treat everyone with respect and consideration
- **Be collaborative**: Share knowledge and help each other grow
- **Be constructive**: Provide helpful feedback and accept it gracefully
- **Be professional**: Keep discussions focused and productive
- **Be inclusive**: Welcome diverse perspectives and experiences

### Unacceptable Behavior

- Harassment, discrimination, or disrespectful comments
- Personal attacks or inflammatory remarks
- Publishing others' private information without permission
- Any behavior that would be inappropriate in a professional setting

### Reporting

If you experience or witness unacceptable behavior, please report it to the project maintainers. All reports will be handled with discretion and confidentiality.

## Questions?

Don't hesitate to ask questions! We're here to help:

- **Not sure where to start?** Check out issues labeled `good first issue` or `help wanted`
- **Stuck on something?** Open a draft PR early and ask for feedback
- **Need clarification?** Comment on the relevant issue or PR

Remember, there are no stupid questions - we're all learning together! 🚀

---

Thank you for contributing to MindSpace! Your efforts help us build better tools for understanding and preventing student burnout. Every contribution, no matter how small, makes a difference. Happy coding! 💙
