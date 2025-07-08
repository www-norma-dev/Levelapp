// File: src/components/ScenarioPresets/JsonCodeEditor.tsx
"use client";

import React from "react";
import CodeMirror from "@uiw/react-codemirror";
import { json } from "@codemirror/lang-json";
import { EditorView } from "@codemirror/view";

interface JsonCodeEditorProps {
  value: any;
  onChange: (updated: any) => void;
  height?: string; // e.g. "400px"
}

export function JsonCodeEditor({
  value,
  onChange,
  height = "400px",
}: JsonCodeEditorProps) {
  // Local state to keep the editor text in sync
  const [code, setCode] = React.useState(() => JSON.stringify(value, null, 2));

  // When `value` prop changes, update the editor text
  React.useEffect(() => {
    setCode(JSON.stringify(value, null, 2));
  }, [value]);

  return (
    <CodeMirror
      value={code}
      height={height}
      extensions={[
        json(),
        EditorView.lineWrapping, // ← enable line wrap
      ]}
      basicSetup={{
        lineNumbers: true,
        highlightActiveLineGutter: true,
        foldGutter: true,
        allowMultipleSelections: true,
      }}
      onChange={(newCode) => {
        setCode(newCode);
        try {
          const parsed = JSON.parse(newCode);
          onChange(parsed);
        } catch {
          // ignore invalid JSON until it's corrected
        }
      }}
      style={{
        width: "100%", // ensure full-width
        border: "1px solid #2d2d2d",
        borderRadius: "8px",
        fontFamily: "monospace",
        fontSize: "0.9rem",
      }}
    />
  );
}
