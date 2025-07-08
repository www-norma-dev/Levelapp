// File: hooks/useFirebaseUpload.ts
import { useState } from "react";
import { ref, uploadBytesResumable, getDownloadURL } from "firebase/storage";
import { storage } from "@/lib/firebase";

export interface UploadedFile {
  name: string;
  url: string;
  folder: string; // now: uploadPath
  content_type: string;
  id: string; // random UUID
}

/**
 * @param userId     your current user ID
 * @param uploadPath subfolder under your userId (e.g. presetName)
 */
export function useFirebaseUpload(
  userId: string | undefined,
  uploadPath: string = ""
) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [progresses, setProgresses] = useState<Record<string, number>>({});
  const [isUploading, setIsUploading] = useState(false);

  const upload = async (
    files: File[],
    onFinish?: (uploaded: UploadedFile[]) => void
  ) => {
    if (!userId) {
      console.error("Missing userId during upload");
      return;
    }

    setIsUploading(true);
    const uploaded: UploadedFile[] = [];

    for (const file of files) {
      const id = crypto.randomUUID();
      // build path: uploads/userId/uploadPath/file.name
      const pathParts = ["uploads", userId]
        .concat(uploadPath ? [uploadPath] : [])
        .concat(file.name);
      const fullPath = pathParts.join("/");

      const fileRef = ref(storage, fullPath);
      const uploadTask = uploadBytesResumable(fileRef, file);

      await new Promise<void>((resolve, reject) => {
        uploadTask.on(
          "state_changed",
          (snapshot) => {
            const progress =
              (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            setProgresses((prev) => ({
              ...prev,
              [file.name]: progress,
            }));
          },
          reject,
          async () => {
            const url = await getDownloadURL(uploadTask.snapshot.ref);
            uploaded.push({
              name: file.name,
              url,
              folder: uploadPath, // report which subfolder it went into
              content_type: file.type,
              id,
            });
            resolve();
          }
        );
      });
    }

    setUploadedFiles((prev) => [...prev, ...uploaded]);
    setIsUploading(false);
    setProgresses({});
    onFinish?.(uploaded);
  };

  return { upload, uploadedFiles, isUploading, progresses };
}
