// File: src/app/dashboard/settings/page.tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { clientAuth } from "@/lib/firebase";
import { Input } from "@/components/ui/input";
import {
  updatePassword,
  reauthenticateWithCredential,
  signInWithEmailAndPassword,
  EmailAuthProvider,
} from "firebase/auth";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Copy } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { MoreVertical } from "lucide-react";

export default function SettingsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"general" | "security" | "team">(
    "general"
  );
  const { toast } = useToast();

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    const email = session?.user?.email || "";
    let firebaseUser = clientAuth.currentUser;

    try {
      if (!firebaseUser) {
        const userCredential = await signInWithEmailAndPassword(
          clientAuth,
          email,
          currentPassword
        );
        firebaseUser = userCredential.user;
      } else {
        const credential = EmailAuthProvider.credential(email, currentPassword);
        await reauthenticateWithCredential(firebaseUser, credential);
      }
      await updatePassword(firebaseUser, newPassword);
      setMessage("Password updated successfully!");
      setTimeout(() => {
        router.push("/dashboard/overview");
      }, 2000);
    } catch (err: any) {
      console.error("Password update error:", err);
      setError(err.message || "Error updating password.");
    }
  };

  const handleCopyAccountId = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (session?.user?.id) {
      navigator.clipboard.writeText(session.user.id);
      toast({ description: "Your Account ID Copied!" });
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md mt-10 flex">
      {/* Sidebar Navigation */}
      <div className="w-1/4 border-r p-4 space-y-2">
        <Button
          variant={activeTab === "general" ? "default" : "ghost"}
          className="w-full justify-start"
          onClick={() => setActiveTab("general")}
        >
          General
        </Button>
        <Button
          variant={activeTab === "security" ? "default" : "ghost"}
          className="w-full justify-start"
          onClick={() => setActiveTab("security")}
        >
          Security
        </Button>
        <Button
          variant={activeTab === "team" ? "default" : "ghost"}
          className="w-full justify-start"
          onClick={() => setActiveTab("team")}
        >
          Team Management
        </Button>
      </div>

      {/* Content Section */}
      <div className="w-3/4 p-6">
        {activeTab === "general" && (
          <>
            <h2 className="text-2xl font-semibold mb-6">General Settings</h2>

            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">
                Profile Information
              </h3>
              <p className="mb-2">{session?.user?.email}</p>

              <div className="flex justify-between items-center bg-gray-50 gap-2 p-2 rounded-lg">
                <div>
                  <p className="font-bold">Your ID:</p>
                  <p className="font-mono">
                    {session?.user?.id?.replace(/./g, "*")}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleCopyAccountId}
                >
                  <Copy className="w-5 h-5 text-gray-600" />
                </Button>
              </div>
            </div>
          </>
        )}
        {activeTab === "team" && (
          <>
            <h2 className="text-2xl font-semibold mb-6">Team Management</h2>

            <TeamManagementSection />
          </>
        )}

        {activeTab === "security" && (
          <>
            <h2 className="text-2xl font-semibold mb-6">Security Settings</h2>

            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Change Password</h3>

              <form onSubmit={handleChangePassword} className="space-y-4">
                <Input
                  type="password"
                  placeholder="Current Password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <Input
                  type="password"
                  placeholder="New Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <Input
                  type="password"
                  placeholder="Confirm New Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />

                <Button type="submit" className="w-full">
                  Change Password
                </Button>
              </form>

              {message && (
                <p className="text-green-600 text-center mt-4">{message}</p>
              )}
              {error && (
                <p className="text-red-600 text-center mt-4">{error}</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
function TeamManagementSection() {
  const [search, setSearch] = React.useState("");

  const mockTeam = [
    { name: "Tariq Sadi", username: "tsadi", role: "Member" },
    { name: "Tariq Sadi", username: "tsadi", role: "Member" },
    { name: "Tariq Sadi", username: "tsadi", role: "Owner" },
    { name: "Jonas Weber", username: "jweber", role: "Member" },
    { name: "Lina Ortega", username: "lortega", role: "Member" },
  ];

  const filteredTeam = mockTeam.filter((member) =>
    member.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <Input
          placeholder="Search members"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm"
        />
        <Button className="ml-4">Invite</Button>
      </div>

      <div className="space-y-4">
        {filteredTeam.map((member, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between border p-3 rounded-md bg-muted/20"
          >
            <div className="flex items-center gap-4">
              <Avatar>
                <AvatarFallback>
                  {member.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium">{member.name}</p>
                <p className="text-sm text-muted-foreground">
                  @{member.username}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Select defaultValue={member.role}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Owner">Owner</SelectItem>
                  <SelectItem value="Member">Member</SelectItem>
                  <SelectItem value="Viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => alert(`Viewing ${member.name}`)}
                  >
                    View Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => alert(`Editing ${member.name}`)}
                  >
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => alert(`Removing ${member.name}`)}
                  >
                    Remove
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
