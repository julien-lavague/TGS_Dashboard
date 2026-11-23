"use client";

import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type {
  ReleaseNoteAudience,
  ReleaseNoteCategory,
  ReleaseNoteItem,
} from "@/lib/types";

const CATEGORIES: { id: ReleaseNoteCategory; label: string; color: string }[] = [
  { id: "major", label: "Majeur", color: "#006d9a" },
  { id: "minor", label: "Mineur", color: "#048b94" },
  { id: "fix", label: "Corrections", color: "#94a3b8" },
];

const AUDIENCES: { id: ReleaseNoteAudience; label: string }[] = [
  { id: "all", label: "All" },
  { id: "free", label: "Free" },
  { id: "premium", label: "Premium" },
];

interface DraftItem extends ReleaseNoteItem {
  key: string;
}

function newKey() {
  return Math.random().toString(36).slice(2, 10);
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function formatFrench(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

export default function ReleaseNotesPage() {
  const queryClient = useQueryClient();

  const [version, setVersion] = useState("");
  const [publishedAt, setPublishedAt] = useState(todayISO());
  const [audience, setAudience] = useState<ReleaseNoteAudience>("all");
  const [isImportant, setIsImportant] = useState(true);
  const [items, setItems] = useState<DraftItem[]>([
    { key: newKey(), category: "major", title: "", description: null, image_url: null },
  ]);
  const [error, setError] = useState<string | null>(null);

  const notes = useQuery({ queryKey: ["release-notes"], queryFn: api.releaseNotes.list });

  const publish = useMutation({
    mutationFn: () =>
      api.releaseNotes.create({
        version: version.trim(),
        // The app compares this to the account creation date, so send a real instant
        published_at: new Date(`${publishedAt}T09:00:00`).toISOString(),
        is_important: isImportant,
        audience,
        items: items
          .filter((item) => item.title.trim().length > 0)
          .map(({ key: _key, ...item }) => ({
            ...item,
            title: item.title.trim(),
            description: item.description?.trim() || null,
          })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["release-notes"] });
      setVersion("");
      setItems([{ key: newKey(), category: "major", title: "", description: null, image_url: null }]);
      setError(null);
    },
    onError: (mutationError: unknown) => {
      const detail =
        (mutationError as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (mutationError as Error)?.message;
      setError(detail || "Publication failed");
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.releaseNotes.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["release-notes"] }),
  });

  const filledItems = useMemo(
    () => items.filter((item) => item.title.trim().length > 0),
    [items]
  );
  const canPublish = version.trim().length > 0 && filledItems.length > 0 && !publish.isPending;

  function updateItem(key: string, patch: Partial<DraftItem>) {
    setItems((current) => current.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  function addItem(category: ReleaseNoteCategory) {
    setItems((current) => [
      ...current,
      { key: newKey(), category, title: "", description: null, image_url: null },
    ]);
  }

  function removeItem(key: string) {
    setItems((current) => current.filter((item) => item.key !== key));
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Release Notes</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Publish a changelog entry to the TheGoodSpots app
          </p>
        </div>
        <Button onClick={() => publish.mutate()} disabled={!canPublish}>
          {publish.isPending ? "Publishing…" : "Publish"}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg bg-destructive/10 text-destructive px-4 py-3 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-6 items-start">
        <Card>
          <CardHeader className="border-b">
            <CardTitle>New entry</CardTitle>
            <CardDescription>Goes live in the app as soon as you publish</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Version">
                <input
                  value={version}
                  onChange={(event) => setVersion(event.target.value)}
                  placeholder="v2.1.0"
                  className="h-8 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring"
                />
              </Field>
              <Field label="Publication date">
                <input
                  type="date"
                  value={publishedAt}
                  onChange={(event) => setPublishedAt(event.target.value)}
                  className="h-8 w-full rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring"
                />
              </Field>
            </div>

            <Field label="Audience">
              <div className="flex flex-wrap gap-2">
                {AUDIENCES.map((option) => (
                  <Button
                    key={option.id}
                    size="sm"
                    variant={audience === option.id ? "default" : "outline"}
                    onClick={() => setAudience(option.id)}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </Field>

            <label className="flex items-start gap-3 rounded-lg bg-muted p-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isImportant}
                onChange={(event) => setIsImportant(event.target.checked)}
                className="mt-0.5 size-4 accent-primary"
              />
              <span>
                <span className="block text-sm font-medium">Important</span>
                <span className="block text-[13px] leading-[18px] text-muted-foreground">
                  Blocking modal on next open. Unchecked, the entry only feeds the badge and the panel.
                </span>
              </span>
            </label>

            <div className="h-px bg-border" />

            {CATEGORIES.map((category) => (
              <div key={category.id} className="space-y-2">
                <span
                  className="text-[11px] font-semibold uppercase tracking-wider"
                  style={{ color: category.color }}
                >
                  {category.label}
                </span>

                {items
                  .filter((item) => item.category === category.id)
                  .map((item) => (
                    <ItemRow
                      key={item.key}
                      item={item}
                      onChange={(patch) => updateItem(item.key, patch)}
                      onRemove={() => removeItem(item.key)}
                    />
                  ))}

                <button
                  type="button"
                  onClick={() => addItem(category.id)}
                  className="text-[13px] text-muted-foreground hover:text-foreground transition-colors"
                >
                  + Add a line
                </button>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
              <CardDescription>As it appears in the app</CardDescription>
            </CardHeader>
            <CardContent>
              <ModalPreview
                version={version || "v?.?.?"}
                publishedAt={publishedAt}
                items={filledItems}
              />
              <dl className="mt-4 space-y-2 text-[13px]">
                <div className="flex items-center justify-between">
                  <dt className="text-muted-foreground">Audience</dt>
                  <dd className="font-medium">
                    {audience === "all" ? "All accounts" : audience === "free" ? "Free accounts" : "Premium accounts"}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-muted-foreground">Display</dt>
                  <dd className="font-medium">{isImportant ? "Blocking, once" : "Badge and panel only"}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Published</CardTitle>
              <CardDescription>
                {notes.data ? `${notes.data.rows.length} entries` : "Loading…"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {notes.data?.rows.map((note) => (
                <div
                  key={note.id}
                  className="flex items-center gap-2 rounded-lg border px-3 py-2"
                >
                  <span className="text-sm font-medium">{note.version}</span>
                  {note.is_important && <Badge variant="secondary">important</Badge>}
                  {note.audience !== "all" && <Badge variant="outline">{note.audience}</Badge>}
                  <span className="flex-1" />
                  <span className="text-xs text-muted-foreground">{formatFrench(note.published_at)}</span>
                  <Button
                    size="xs"
                    variant="destructive"
                    onClick={() => remove.mutate(note.id)}
                    disabled={remove.isPending}
                  >
                    Delete
                  </Button>
                </div>
              ))}
              {notes.data?.rows.length === 0 && (
                <p className="text-sm text-muted-foreground">Nothing published yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}</label>
      {children}
    </div>
  );
}

function ItemRow({
  item,
  onChange,
  onRemove,
}: {
  item: DraftItem;
  onChange: (patch: Partial<DraftItem>) => void;
  onRemove: () => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const { image_url } = await api.releaseNotes.uploadImage(file);
      onChange({ image_url });
    } catch (error) {
      const detail =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (error as Error)?.message;
      setUploadError(detail || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <input
          value={item.title}
          onChange={(event) => onChange({ title: event.target.value })}
          placeholder="Ce que l&apos;utilisateur va lire"
          className="h-8 flex-1 rounded-lg border bg-background px-3 text-sm outline-none focus-visible:border-ring"
        />
        <Button size="icon-sm" variant="ghost" onClick={onRemove} aria-label="Remove line">
          ✕
        </Button>
      </div>

      {item.description !== null && (
        <input
          value={item.description ?? ""}
          onChange={(event) => onChange({ description: event.target.value })}
          placeholder="Description (facultative)"
          className="h-8 w-full rounded-lg border bg-background px-3 text-[13px] outline-none focus-visible:border-ring"
        />
      )}

      {item.image_url && (
        <div className="flex items-center gap-3 rounded-lg border border-dashed bg-muted p-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.image_url}
            alt=""
            className="h-10 w-[66px] rounded-md border object-cover object-left-top"
          />
          <span className="flex-1 truncate text-[13px] text-muted-foreground">
            Shown under this line, in the app modal
          </span>
          <Button size="xs" variant="ghost" onClick={() => onChange({ image_url: null })}>
            Remove
          </Button>
        </div>
      )}

      <div className="flex items-center gap-4 text-[13px] text-muted-foreground">
        {item.description === null && (
          <button
            type="button"
            onClick={() => onChange({ description: "" })}
            className="hover:text-foreground transition-colors"
          >
            + Description
          </button>
        )}
        {!item.image_url && (
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={uploading}
            className="hover:text-foreground transition-colors disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "+ Add an image"}
          </button>
        )}
        {uploadError && <span className="text-destructive">{uploadError}</span>}
      </div>

      <input
        ref={fileInput}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        className="hidden"
        onChange={(event) => handleFile(event.target.files?.[0])}
      />
    </div>
  );
}

/**
 * Reproduction de la modale telle qu'elle sort dans l'app (charte marine),
 * pour vérifier le rendu avant publication.
 */
function ModalPreview({
  version,
  publishedAt,
  items,
}: {
  version: string;
  publishedAt: string;
  items: ReleaseNoteItem[];
}) {
  return (
    <div className="rounded-xl bg-muted p-4">
      <div className="rounded-[14px] border border-sky-200 bg-white p-4 text-slate-900">
        <div className="flex items-start gap-2.5">
          <div className="rounded-[10px] bg-sky-100 p-1.5 text-sky-600">✦</div>
          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-semibold">Nouveautés</span>
              <span className="rounded-full bg-gradient-to-r from-sky-500 to-blue-600 px-[7px] py-px text-[11px] font-medium text-white">
                {version}
              </span>
            </div>
            <p className="mt-px text-[11px] text-slate-500">
              Mise en ligne le {formatFrench(publishedAt)}
            </p>
          </div>
        </div>

        <div className="mt-3 space-y-[7px]">
          {items.length === 0 && (
            <p className="text-[12px] text-slate-400">Ajoute une ligne pour voir le rendu.</p>
          )}
          {items.map((item, index) => {
            const color = CATEGORIES.find((category) => category.id === item.category)?.color;
            return (
              <div key={index} className="space-y-[7px]">
                <div className="flex gap-2">
                  <span
                    className="mt-1.5 size-[5px] shrink-0 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <div>
                    <p
                      className={`text-[12px] leading-[17px] ${
                        item.description ? "font-medium text-slate-900" : "text-slate-600"
                      }`}
                    >
                      {item.title}
                    </p>
                    {item.description && (
                      <p className="text-[12px] leading-[17px] text-slate-500">{item.description}</p>
                    )}
                  </div>
                </div>
                {item.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={item.image_url}
                    alt=""
                    className="w-full rounded-lg border border-sky-200"
                  />
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-3 flex justify-end">
          <span className="inline-flex h-[30px] items-center rounded-md bg-gradient-to-r from-[#006d9a] to-[#3a9f6f] px-3.5 text-[12px] font-medium text-white">
            Compris
          </span>
        </div>
      </div>
    </div>
  );
}
