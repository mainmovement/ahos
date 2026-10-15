"use client";
import { useEffect, useRef, useState } from "react";
import { ArrowUpLeft, Search, X } from "lucide-react";
import { allItems, type Language } from "../../lib/navigation";

export function CommandPalette({
  open,
  onClose,
  onNavigate,
  language,
}: {
  open: boolean;
  onClose: () => void;
  onNavigate: (id: string) => void;
  language: Language;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState("");
  const fa = language === "fa";
  const items = allItems.filter((item) =>
    `${item.fa} ${item.en}`.toLowerCase().includes(query.toLowerCase().trim()),
  );
  useEffect(() => {
    const dialog = ref.current;
    if (open && !dialog?.open) dialog?.showModal();
    else if (!open && dialog?.open) dialog.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      className="ah-command-dialog"
      aria-labelledby="command-title"
      onCancel={onClose}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      onKeyDown={(event) => {
        if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
        event.preventDefault();
        const controls = Array.from(
          ref.current?.querySelectorAll<HTMLElement>(
            "input, .ah-command-result",
          ) ?? [],
        );
        const index = controls.indexOf(document.activeElement as HTMLElement);
        controls[
          (index + (event.key === "ArrowDown" ? 1 : -1) + controls.length) %
            controls.length
        ]?.focus();
      }}
    >
      <div className="ah-command-search">
        <Search size={20} />
        <label
          id="command-title"
          className="ah-sr-only"
          htmlFor="command-search"
        >
          {fa ? "جست‌وجوی بخش‌ها" : "Search sections"}
        </label>
        <input
          id="command-search"
          autoFocus
          autoComplete="off"
          placeholder={
            fa ? "کجا می‌خواهید بروید؟" : "Where would you like to go?"
          }
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && items[0]) {
              onNavigate(items[0].id);
              onClose();
            }
          }}
        />
        <button
          className="ah-icon-button"
          onClick={onClose}
          aria-label={fa ? "بستن" : "Close"}
        >
          <X size={18} />
        </button>
      </div>
      <div className="ah-command-heading">
        {fa
          ? "بخش‌های فضای کاری · صفحات در مراحل بعد"
          : "WORKSPACE SECTIONS · PAGES IN LATER STAGES"}
      </div>
      <div className="ah-command-results">
        {items.map((item) => (
          <button
            className="ah-command-result"
            key={item.id}
            onClick={() => {
              onNavigate(item.id);
              onClose();
            }}
          >
            <item.icon size={18} />
            <span>{item[language]}</span>
            <small>{item.en}</small>
            <ArrowUpLeft size={14} />
          </button>
        ))}
        {items.length === 0 && (
          <p className="ah-command-empty">
            {fa
              ? "نتیجه‌ای پیدا نشد. عبارت دیگری امتحان کنید."
              : "No results. Try another search."}
          </p>
        )}
      </div>
      <footer className="ah-command-footer">
        <span>
          ↑ ↓ {fa ? "حرکت" : "Navigate"} · ↵ {fa ? "انتخاب" : "Select"}
        </span>
        <span>ESC {fa ? "بستن" : "Close"}</span>
      </footer>
    </dialog>
  );
}
