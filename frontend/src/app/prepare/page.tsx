"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { deleteSession, getChecklist, getPacketUrl, type ChecklistItem } from "@/lib/api";

export default function PreparePage() {
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [householdSize] = useState(4);

  useEffect(() => {
    getChecklist().then((result) => setItems(result.items));
  }, []);

  async function handleDelete() {
    await deleteSession();
    setItems([]);
    window.location.href = "/profile";
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Step 3: Prepare</h1>

      <Card className="space-y-2 p-4">
        <h2 className="font-medium">Checklist</h2>
        <ul className="space-y-1">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-2">
              <span aria-hidden="true">{item.status === "present" ? "✓" : "✗"}</span>
              <span>
                {item.label} — <strong>{item.status}</strong>
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="flex gap-3 p-4">
        <a href={getPacketUrl(householdSize, "60")}>
          <Button>Download packet</Button>
        </a>
        <Button variant="destructive" onClick={handleDelete}>
          Delete my session
        </Button>
      </Card>
    </main>
  );
}
