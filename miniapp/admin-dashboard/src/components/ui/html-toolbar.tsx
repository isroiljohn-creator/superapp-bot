import { useRef, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Toggle } from "@/components/ui/toggle";
import { Bold, Italic, Link, Code } from "lucide-react";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useState } from "react";

interface HtmlToolbarProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    rows?: number;
}

export function HtmlToolbar({ value, onChange, placeholder, rows = 3 }: HtmlToolbarProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [linkOpen, setLinkOpen] = useState(false);
    const [linkUrl, setLinkUrl] = useState("");
    const [linkText, setLinkText] = useState("");

    const wrapSelection = useCallback((tagOpen: string, tagClose: string) => {
        const el = textareaRef.current;
        if (!el) return;

        const start = el.selectionStart;
        const end = el.selectionEnd;
        const selected = value.substring(start, end);
        const before = value.substring(0, start);
        const after = value.substring(end);

        if (selected) {
            // Wrap selected text
            const newValue = before + tagOpen + selected + tagClose + after;
            onChange(newValue);
            // Restore cursor after the wrapped text
            requestAnimationFrame(() => {
                el.focus();
                el.selectionStart = start + tagOpen.length;
                el.selectionEnd = end + tagOpen.length;
            });
        } else {
            // No selection — insert placeholder
            const placeholder = tagOpen === "<b>" ? "qalin matn" : tagOpen === "<i>" ? "kursiv matn" : "matn";
            const newValue = before + tagOpen + placeholder + tagClose + after;
            onChange(newValue);
            requestAnimationFrame(() => {
                el.focus();
                el.selectionStart = start + tagOpen.length;
                el.selectionEnd = start + tagOpen.length + placeholder.length;
            });
        }
    }, [value, onChange]);

    const handleBold = useCallback(() => wrapSelection("<b>", "</b>"), [wrapSelection]);
    const handleItalic = useCallback(() => wrapSelection("<i>", "</i>"), [wrapSelection]);
    const handleCode = useCallback(() => wrapSelection("<code>", "</code>"), [wrapSelection]);

    const handleInsertLink = useCallback(() => {
        const el = textareaRef.current;
        if (!el) return;

        const url = linkUrl.trim();
        const text = linkText.trim() || url;
        if (!url) return;

        const start = el.selectionStart;
        const end = el.selectionEnd;
        const before = value.substring(0, start);
        const after = value.substring(end);

        const tag = `<a href="${url}">${text}</a>`;
        const newValue = before + tag + after;
        onChange(newValue);

        setLinkUrl("");
        setLinkText("");
        setLinkOpen(false);

        requestAnimationFrame(() => {
            el.focus();
            el.selectionStart = start + tag.length;
            el.selectionEnd = start + tag.length;
        });
    }, [value, onChange, linkUrl, linkText]);

    // Handle keyboard shortcuts
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "b") {
            e.preventDefault();
            handleBold();
        } else if ((e.metaKey || e.ctrlKey) && e.key === "i") {
            e.preventDefault();
            handleItalic();
        }
    }, [handleBold, handleItalic]);

    return (
        <div className="space-y-1.5">
            {/* Toolbar */}
            <div className="flex items-center gap-0.5 p-1 bg-secondary/30 rounded-lg border border-border">
                <Toggle
                    size="sm"
                    aria-label="Bold"
                    onPressedChange={handleBold}
                    pressed={false}
                    className="h-7 w-7 p-0 data-[state=on]:bg-primary/20"
                    title="Qalin (Ctrl+B)"
                >
                    <Bold className="h-3.5 w-3.5" />
                </Toggle>

                <Toggle
                    size="sm"
                    aria-label="Italic"
                    onPressedChange={handleItalic}
                    pressed={false}
                    className="h-7 w-7 p-0 data-[state=on]:bg-primary/20"
                    title="Kursiv (Ctrl+I)"
                >
                    <Italic className="h-3.5 w-3.5" />
                </Toggle>

                <Toggle
                    size="sm"
                    aria-label="Code"
                    onPressedChange={handleCode}
                    pressed={false}
                    className="h-7 w-7 p-0 data-[state=on]:bg-primary/20"
                    title="Kod"
                >
                    <Code className="h-3.5 w-3.5" />
                </Toggle>

                <div className="w-px h-5 bg-border mx-0.5" />

                <Popover open={linkOpen} onOpenChange={setLinkOpen}>
                    <PopoverTrigger asChild>
                        <button
                            type="button"
                            className="inline-flex items-center justify-center h-7 w-7 rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none"
                            title="Havola qo'shish"
                        >
                            <Link className="h-3.5 w-3.5" />
                        </button>
                    </PopoverTrigger>
                    <PopoverContent className="w-72 p-3" align="start">
                        <div className="space-y-3">
                            <p className="text-sm font-medium">🔗 Havola qo'shish</p>
                            <div className="space-y-1.5">
                                <Label className="text-xs">URL</Label>
                                <Input
                                    value={linkUrl}
                                    onChange={(e) => setLinkUrl(e.target.value)}
                                    placeholder="https://..."
                                    className="h-8 text-sm"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Ko'rinadigan matn</Label>
                                <Input
                                    value={linkText}
                                    onChange={(e) => setLinkText(e.target.value)}
                                    placeholder="Bu yerga bosing"
                                    className="h-8 text-sm"
                                />
                            </div>
                            <Button
                                type="button"
                                size="sm"
                                className="w-full h-8"
                                onClick={handleInsertLink}
                                disabled={!linkUrl.trim()}
                            >
                                Qo'shish
                            </Button>
                        </div>
                    </PopoverContent>
                </Popover>
            </div>

            {/* Textarea */}
            <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                rows={rows}
                className="font-mono text-sm"
            />
        </div>
    );
}
