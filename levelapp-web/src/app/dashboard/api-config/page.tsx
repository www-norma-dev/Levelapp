// components/SchemaBuilderUI.tsx
"use client";

import React, { useState, useMemo } from "react";
import YAML from "yaml";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

type ParamDef = {
  id: string;
  name: string;
  in: "header" | "query";
  required: boolean;
  schemaType: string;
  defaultValue?: string;
};

type SchemaDef = {
  id: string;
  name: string;
  json: string;
};

type PathDef = {
  id: string;
  path: string;
  method: "get" | "post" | "put" | "delete";
  reqSchema: string;
  resSchema: string;
  paramRefs: string[];
};

// Recursively collect all "dotted" property paths from an object schema
function getAllPaths(schema: any, base = ""): string[] {
  if (!schema || schema.type !== "object" || !schema.properties) return [];
  return Object.entries(schema.properties).flatMap(([key, subschema]: any) => {
    const path = base ? `${base}.${key}` : key;
    return [path, ...getAllPaths(subschema, path)];
  });
}

const SchemaBuilderUI: React.FC = () => {
  // 1) OpenAPI Builder State
  const [title, setTitle] = useState("RAG-Powered Chatbot");
  const [version, setVersion] = useState("1.0.0");
  const [baseUrl, setBaseUrl] = useState("https://api.example.com");

  const [params, setParams] = useState<ParamDef[]>([]);
  const [schemas, setSchemas] = useState<SchemaDef[]>([]);
  const [paths, setPaths] = useState<PathDef[]>([]);

  // 2) Field Mapping State
  const [mappingPathId, setMappingPathId] = useState<string>("");
  const [requestField, setRequestField] = useState<string>("");
  const [responseField, setResponseField] = useState<string>("");
  const [metadataFields, setMetadataFields] = useState<string[]>([]);

  // Helpers to add rows
  const addParam = () =>
    setParams((ps) => [
      ...ps,
      {
        id: crypto.randomUUID(),
        name: "",
        in: "header",
        required: false,
        schemaType: "string",
      },
    ]);
  const addSchema = () =>
    setSchemas((ss) => [
      ...ss,
      { id: crypto.randomUUID(), name: "", json: "{\n\n}" },
    ]);
  const addPath = () =>
    setPaths((pp) => [
      ...pp,
      {
        id: crypto.randomUUID(),
        path: "",
        method: "post",
        reqSchema: "",
        resSchema: "",
        paramRefs: [],
      },
    ]);

  // Update handlers
  const updateParam = (id: string, field: keyof ParamDef, val: any) =>
    setParams((ps) =>
      ps.map((p) => (p.id === id ? { ...p, [field]: val } : p))
    );
  const updateSchema = (id: string, field: keyof SchemaDef, val: any) =>
    setSchemas((ss) =>
      ss.map((s) => (s.id === id ? { ...s, [field]: val } : s))
    );
  const updatePath = (id: string, field: keyof PathDef, val: any) =>
    setPaths((pp) =>
      pp.map((p) => {
        if (p.id !== id) return p;
        if (field === "paramRefs") {
          const arr = Array.isArray(val) ? val : val != null ? [val] : [];
          return { ...p, paramRefs: arr };
        }
        return { ...p, [field]: val };
      })
    );

  // Build in-memory OpenAPI spec
  const buildSpec = () => {
    const spec: any = {
      openapi: "3.0.0",
      info: { title, version },
      servers: [{ url: baseUrl }],
      paths: {},
      components: { parameters: {}, schemas: {} },
    };

    // Parameters
    params.forEach((p) => {
      spec.components.parameters[p.name] = {
        name: p.name,
        in: p.in,
        required: p.required,
        schema: {
          type: p.schemaType,
          ...(p.defaultValue ? { default: p.defaultValue } : {}),
        },
      };
    });

    // Schemas
    schemas.forEach((s) => {
      try {
        spec.components.schemas[s.name] = JSON.parse(s.json);
      } catch {
        console.warn(`Invalid JSON for schema "${s.name}"`);
      }
    });

    // Paths
    paths.forEach((p) => {
      if (!spec.paths[p.path]) spec.paths[p.path] = {};
      spec.paths[p.path][p.method] = {
        parameters: p.paramRefs
          .map((id) => params.find((x) => x.id === id))
          .filter(Boolean)
          .map((pr) => ({ $ref: `#/components/parameters/${pr!.name}` })),
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: { $ref: `#/components/schemas/${p.reqSchema}` },
            },
          },
        },
        responses: {
          "200": {
            description: "OK",
            content: {
              "application/json": {
                schema: { $ref: `#/components/schemas/${p.resSchema}` },
              },
            },
          },
        },
      };
    });

    return spec;
  };

  const spec = useMemo(buildSpec, [
    title,
    version,
    baseUrl,
    params,
    schemas,
    paths,
  ]);

  // Derive mapping options for the selected path
  const selectedPath = paths.find((p) => p.id === mappingPathId);

  let reqOptions: string[] = [];
  let resOptions: string[] = [];
  let metaOptions: string[] = [];

  if (selectedPath) {
    // Request schema flatten
    const reqSchemaObj = spec.components.schemas[selectedPath.reqSchema];
    if (reqSchemaObj) {
      reqOptions = getAllPaths(reqSchemaObj);
    }
    // Response schema flatten
    const resSchemaObj = spec.components.schemas[selectedPath.resSchema];
    if (resSchemaObj) {
      resOptions = getAllPaths(resSchemaObj);
    }
    // Metadata options = everything except the primaries
    metaOptions = Array.from(
      new Set(
        [...reqOptions, ...resOptions].filter(
          (p) => p !== requestField && p !== responseField
        )
      )
    );
  }

  // Export OpenAPI YAML
  const exportYAML = () => {
    const yaml = YAML.stringify(spec);
    const blob = new Blob([yaml], { type: "application/x-yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "openapi.yaml";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">API Schema Builder</h1>
      <Tabs defaultValue="info">
        <TabsList>
          <TabsTrigger value="info">API Info</TabsTrigger>
          <TabsTrigger value="params">Parameters</TabsTrigger>
          <TabsTrigger value="schemas">Schemas</TabsTrigger>
          <TabsTrigger value="paths">Paths</TabsTrigger>
          <TabsTrigger value="mapping">Field Mapping</TabsTrigger>
        </TabsList>

        {/* Info Tab */}
        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>API Information</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label>Title</Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div>
                <Label>Version</Label>
                <Input
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                />
              </div>
              <div>
                <Label>Base URL</Label>
                <Input
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Params Tab */}
        <TabsContent value="params">
          <Card>
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addParam}>Add Parameter</Button>
              {params.map((p) => (
                <Card key={p.id}>
                  <CardContent className="grid grid-cols-1 sm:grid-cols-5 gap-4">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={p.name}
                        onChange={(e) =>
                          updateParam(p.id, "name", e.target.value)
                        }
                      />
                    </div>
                    <div>
                      <Label>In</Label>
                      <Select
                        value={p.in}
                        onValueChange={(v) => updateParam(p.id, "in", v as any)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="header">header</SelectItem>
                          <SelectItem value="query">query</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center">
                      <Checkbox
                        checked={p.required}
                        onCheckedChange={(v) =>
                          updateParam(p.id, "required", !!v)
                        }
                      />
                      <Label>Required</Label>
                    </div>
                    <div>
                      <Label>Type</Label>
                      <Input
                        value={p.schemaType}
                        onChange={(e) =>
                          updateParam(p.id, "schemaType", e.target.value)
                        }
                      />
                    </div>
                    <div>
                      <Label>Default</Label>
                      <Input
                        value={p.defaultValue || ""}
                        onChange={(e) =>
                          updateParam(p.id, "defaultValue", e.target.value)
                        }
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schemas Tab */}
        <TabsContent value="schemas">
          <Card>
            <CardHeader>
              <CardTitle>Schemas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addSchema}>Add Schema</Button>
              {schemas.map((s) => (
                <Card key={s.id}>
                  <CardContent className="space-y-2">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={s.name}
                        onChange={(e) =>
                          updateSchema(s.id, "name", e.target.value)
                        }
                      />
                    </div>
                    <div>
                      <Label>Definition (JSON)</Label>
                      <Textarea
                        rows={6}
                        value={s.json}
                        onChange={(e) =>
                          updateSchema(s.id, "json", e.target.value)
                        }
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Paths Tab */}
        <TabsContent value="paths">
          <Card>
            <CardHeader>
              <CardTitle>Paths</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={addPath}>Add Path</Button>
              {paths.map((p) => (
                <Card key={p.id}>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <Label>Path</Label>
                        <Input
                          value={p.path}
                          onChange={(e) =>
                            updatePath(p.id, "path", e.target.value)
                          }
                        />
                      </div>
                      <div>
                        <Label>Method</Label>
                        <Select
                          value={p.method}
                          onValueChange={(v) =>
                            updatePath(p.id, "method", v as any)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="get">GET</SelectItem>
                            <SelectItem value="post">POST</SelectItem>
                            <SelectItem value="put">PUT</SelectItem>
                            <SelectItem value="delete">DELETE</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <Label>Request Schema</Label>
                        <Select
                          value={p.reqSchema}
                          onValueChange={(v) =>
                            updatePath(p.id, "reqSchema", v)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Schema" />
                          </SelectTrigger>
                          <SelectContent>
                            {schemas.map((s) => (
                              <SelectItem key={s.id} value={s.name}>
                                {s.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Response Schema</Label>
                        <Select
                          value={p.resSchema}
                          onValueChange={(v) =>
                            updatePath(p.id, "resSchema", v)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Schema" />
                          </SelectTrigger>
                          <SelectContent>
                            {schemas.map((s) => (
                              <SelectItem key={s.id} value={s.name}>
                                {s.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div>
                      <Label>Parameter Refs</Label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                        {params.map((param) => (
                          <div
                            key={param.id}
                            className="flex items-center space-x-2"
                          >
                            <Checkbox
                              checked={p.paramRefs.includes(param.id)}
                              onCheckedChange={(chk) =>
                                updatePath(
                                  p.id,
                                  "paramRefs",
                                  chk
                                    ? [...p.paramRefs, param.id]
                                    : p.paramRefs.filter((x) => x !== param.id)
                                )
                              }
                            />
                            <Label>{param.name || "(unnamed)"}</Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Field Mapping Tab */}
        <TabsContent value="mapping">
          {!selectedPath ? (
            <Card>
              <CardContent>
                <p className="text-red-600">
                  First select a Path in “Paths” tab, then choose it here:
                </p>
                <Label>Select Path to Map</Label>
                <Select value={mappingPathId} onValueChange={setMappingPathId}>
                  <SelectTrigger>
                    <SelectValue placeholder="— select path —" />
                  </SelectTrigger>
                  <SelectContent>
                    {paths.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.method.toUpperCase()} {p.path}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>
                  Field Mapping for {selectedPath.method.toUpperCase()}{" "}
                  {selectedPath.path}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label>User Message Field</Label>
                  <Select value={requestField} onValueChange={setRequestField}>
                    <SelectTrigger>
                      <SelectValue placeholder="Pick request field" />
                    </SelectTrigger>
                    <SelectContent>
                      {reqOptions.map((p) => (
                        <SelectItem key={p} value={p}>
                          {p}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>AI Response Field</Label>
                  <Select
                    value={responseField}
                    onValueChange={setResponseField}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Pick response field" />
                    </SelectTrigger>
                    <SelectContent>
                      {resOptions.map((p) => (
                        <SelectItem key={p} value={p}>
                          {p}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Optional Metadata Keys</Label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {metaOptions.map((p) => (
                      <div key={p} className="flex items-center space-x-2">
                        <Checkbox
                          checked={metadataFields.includes(p)}
                          onCheckedChange={(chk) =>
                            setMetadataFields((m) =>
                              chk ? [...m, p] : m.filter((x) => x !== p)
                            )
                          }
                        />
                        <span className="font-mono text-sm">{p}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <Card>
                  <CardHeader>
                    <CardTitle>Current Mapping</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm">
                      {JSON.stringify(
                        {
                          path: selectedPath.path,
                          requestField,
                          responseField,
                          metadataFields,
                        },
                        null,
                        2
                      )}
                    </pre>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      <Button onClick={exportYAML}>Generate &amp; Download openapi.yaml</Button>
    </div>
  );
};

export default SchemaBuilderUI;
