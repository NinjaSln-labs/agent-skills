<!-- Extracted verbatim from SKILL.md section 'Configuration'. Edit content in this file; SKILL.md keeps only the pointer. -->

## Configuration

```typescript
// tests/contracts/fixtures/schema-loader.ts
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

export interface OpenAPISpec {
  openapi: string;
  info: { title: string; version: string };
  paths: Record<string, Record<string, PathOperation>>;
  components: { schemas: Record<string, JSONSchema> };
}

export interface PathOperation {
  operationId: string;
  summary?: string;
  parameters?: ParameterObject[];
  requestBody?: RequestBodyObject;
  responses: Record<string, ResponseObject>;
}

export interface JSONSchema {
  type?: string;
  properties?: Record<string, JSONSchema>;
  required?: string[];
  items?: JSONSchema;
  enum?: unknown[];
  format?: string;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  additionalProperties?: boolean | JSONSchema;
}

interface ParameterObject {
  name: string;
  in: string;
  required?: boolean;
  schema: JSONSchema;
}

interface RequestBodyObject {
  required?: boolean;
  content: Record<string, { schema: JSONSchema }>;
}

interface ResponseObject {
  description: string;
  content?: Record<string, { schema: JSONSchema }>;
  headers?: Record<string, { schema: JSONSchema }>;
}

export function loadOpenAPISpec(specPath: string): OpenAPISpec {
  const content = fs.readFileSync(specPath, 'utf-8');
  if (specPath.endsWith('.yaml') || specPath.endsWith('.yml')) {
    return yaml.load(content) as OpenAPISpec;
  }
  return JSON.parse(content);
}

export function loadJSONSchema(schemaPath: string): JSONSchema {
  const content = fs.readFileSync(schemaPath, 'utf-8');
  return JSON.parse(content);
}

export function getResponseSchema(
  spec: OpenAPISpec,
  path: string,
  method: string,
  statusCode: string
): JSONSchema | null {
  const pathObj = spec.paths[path];
  if (!pathObj) return null;

  const operation = pathObj[method.toLowerCase()];
  if (!operation) return null;

  const response = operation.responses[statusCode] || operation.responses['default'];
  if (!response?.content) return null;

  const jsonContent = response.content['application/json'];
  return jsonContent?.schema || null;
}
```

```typescript
// tests/contracts/fixtures/contract-helpers.ts
import Ajv, { ErrorObject } from 'ajv';
import addFormats from 'ajv-formats';
import { JSONSchema } from './schema-loader';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

export interface ValidationResult {
  valid: boolean;
  errors: ErrorObject[] | null;
  summary: string;
}

export function validateAgainstSchema(
  data: unknown,
  schema: JSONSchema
): ValidationResult {
  const validate = ajv.compile(schema);
  const valid = validate(data) as boolean;

  return {
    valid,
    errors: validate.errors || null,
    summary: valid
      ? 'Response matches schema'
      : `Schema violations: ${(validate.errors || [])
          .map((e) => `${e.instancePath} ${e.message}`)
          .join('; ')}`,
  };
}

export function checkBackwardCompatibility(
  oldSchema: JSONSchema,
  newSchema: JSONSchema
): { compatible: boolean; breakingChanges: string[] } {
  const breakingChanges: string[] = [];

  // Check for removed required fields
  const oldRequired = new Set(oldSchema.required || []);
  const newRequired = new Set(newSchema.required || []);
  const oldProperties = oldSchema.properties || {};
  const newProperties = newSchema.properties || {};

  // Removed properties that were in old schema
  for (const prop of Object.keys(oldProperties)) {
    if (!(prop in newProperties)) {
      breakingChanges.push(`Removed property: "${prop}"`);
    }
  }

  // Type changes on existing properties
  for (const [prop, oldPropSchema] of Object.entries(oldProperties)) {
    if (prop in newProperties) {
      const newPropSchema = newProperties[prop];
      if (oldPropSchema.type !== newPropSchema.type) {
        breakingChanges.push(
          `Type changed for "${prop}": ${oldPropSchema.type} -> ${newPropSchema.type}`
        );
      }
    }
  }

  // New required fields (breaking for existing consumers)
  for (const field of newRequired) {
    if (!oldRequired.has(field)) {
      breakingChanges.push(`New required field added: "${field}"`);
    }
  }

  // Enum value removal
  for (const [prop, oldPropSchema] of Object.entries(oldProperties)) {
    if (prop in newProperties && oldPropSchema.enum && newProperties[prop].enum) {
      const removedValues = oldPropSchema.enum.filter(
        (v) => !newProperties[prop].enum!.includes(v)
      );
      if (removedValues.length > 0) {
        breakingChanges.push(
          `Enum values removed from "${prop}": ${removedValues.join(', ')}`
        );
      }
    }
  }

  return {
    compatible: breakingChanges.length === 0,
    breakingChanges,
  };
}
```
