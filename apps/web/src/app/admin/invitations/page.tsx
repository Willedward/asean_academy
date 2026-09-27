import { AdminInvitationsPanel } from "@/components/admin-invitations-panel";
export default function AdminInvitationsPage() {
  return (
    <>
      <h1 className="text-3xl font-extrabold">Student invitations</h1>
      <p>Create invitations and manage access to the beta.</p>
      <AdminInvitationsPanel />
    </>
  );
}
