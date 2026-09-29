# Chromatic Integration (extracted from SKILL.md)

## Setup

```bash
npm install -D chromatic
```

## Configuration

```typescript
// .storybook/main.ts
export default {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: ['@chromatic-com/storybook'],
};
```

## CI Configuration

```yaml
# .github/workflows/chromatic.yml
name: Chromatic
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Publish to Chromatic
        uses: chromaui/action@latest
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          exitZeroOnChanges: true
          exitOnceUploaded: true
          onlyChanged: true
```

## Chromatic Story Configuration

```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  component: Button,
  parameters: {
    chromatic: {
      // Capture multiple viewports
      viewports: [375, 768, 1280],
      // Delay for animations
      delay: 300,
      // Disable animations
      pauseAnimationAtEnd: true,
    },
  },
};

export default meta;

export const Primary: StoryObj<typeof Button> = {
  args: {
    variant: 'primary',
    children: 'Button'
  },
};

export const AllStates: StoryObj<typeof Button> = {
  parameters: {
    chromatic: {
      // Test interaction states
      modes: {
        hover: { pseudo: { hover: true } },
        focus: { pseudo: { focus: true } },
        active: { pseudo: { active: true } },
      },
    },
  },
  render: () => (
    <div style={{ display: 'flex', gap: '1rem' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button disabled>Disabled</Button>
    </div>
  ),
};
```
