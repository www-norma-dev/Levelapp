// File: src/app/dashboard/datasets/page.tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Eye, PlusIcon, Trash2, Copy } from "lucide-react";
import { DataGrid, GridRenderCellParams, GridColDef } from "@mui/x-data-grid";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";

export type Dataset = {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  data: any[];
  type: "structured" | "extracted";
  onView?: (id: string) => void;
};

export default function DatasetManager() {
  const router = useRouter();
  const { toast } = useToast();

  // empty data placeholders
  const [datasets] = useState<Dataset[]>([]);
  const [extractedData] = useState<Dataset[]>([]);
  const [datasetToDelete, setDatasetToDelete] = useState<Dataset | null>(null);

  const confirmDelete = () => {
    setDatasetToDelete(null);
  };

  // typed columns
  const datasetColumns: GridColDef<Dataset>[] = [
    { field: "name", headerName: "Name", flex: 1 },
    { field: "description", headerName: "Description", flex: 2 },
    { field: "createdAt", headerName: "Created At", flex: 1.2 },
    { field: "type", headerName: "Type", width: 130 },
    {
      field: "copyId",
      headerName: "Copy ID",
      sortable: false,
      width: 120,
      renderCell: (params: GridRenderCellParams<Dataset>) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            navigator.clipboard.writeText(params.row.id);
            toast({ description: "Dataset ID Copied!" });
          }}
        >
          <Copy className="w-5 h-5" />
        </Button>
      ),
    },
    {
      field: "actions",
      headerName: "Actions",
      sortable: false,
      width: 150,
      renderCell: (params: GridRenderCellParams<Dataset>) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => params.row.onView?.(params.row.id)}
          >
            <Eye className="w-5 h-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-red-600 hover:bg-red-50"
            onClick={() => setDatasetToDelete(params.row)}
          >
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      ),
    },
  ];

  const extractedColumns: GridColDef<Dataset>[] = [
    { field: "name", headerName: "Name", width: 200 },
    { field: "description", headerName: "Description", flex: 2 },
    { field: "createdAt", headerName: "Created At", flex: 1.2 },
    {
      field: "type",
      headerName: "Type",
      width: 130,
      renderCell: () => <span>Extracted</span>,
    },
    {
      field: "copyId",
      headerName: "Copy ID",
      sortable: false,
      width: 120,
      renderCell: (params: GridRenderCellParams<Dataset>) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            navigator.clipboard.writeText(params.row.id);
            toast({ description: "ID Copied!" });
          }}
        >
          <Copy className="w-5 h-5" />
        </Button>
      ),
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <Button>
        <PlusIcon className="mr-2" />
        Add New Dataset
      </Button>
      <div className="bg-white shadow rounded-lg p-4">
        <h2 className="text-2xl font-semibold mb-4">Manage Datasets</h2>
        {/* Structured Datasets */}
        <DataGrid<Dataset>
          rows={datasets}
          columns={datasetColumns}
          getRowId={(row) => row.id}
          loading={false}
          autoHeight
          pageSizeOptions={[5, 10, 20]}
          initialState={{
            pagination: { paginationModel: { pageSize: 10 } },
          }}
          disableRowSelectionOnClick
        />{" "}
      </div>

      {/* Extracted Data */}
      <div className="bg-white shadow rounded-lg p-4">
        <h2 className="text-2xl font-semibold mb-4">Extracted Data</h2>
        <DataGrid<Dataset>
          rows={extractedData}
          columns={extractedColumns}
          getRowId={(row) => row.id}
          loading={false}
          autoHeight
          pageSizeOptions={[5, 10]}
          initialState={{
            pagination: { paginationModel: { pageSize: 5 } },
          }}
          disableRowSelectionOnClick
        />
      </div>

      {/* Confirm Delete Dialog */}
      {datasetToDelete && (
        <AlertDialog
          open
          onOpenChange={(open) => !open && setDatasetToDelete(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete dataset?</AlertDialogTitle>
              <AlertDialogDescription>
                Permanently delete “{datasetToDelete.name}”?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setDatasetToDelete(null)}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
}
