import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import { useEffect } from 'react'
import {
  Bold, Italic, UnderlineIcon, Link as LinkIcon,
  List, ListOrdered, Minus,
} from 'lucide-react'

interface Props {
  value: string
  onChange: (html: string) => void
  disabled?: boolean
}

const EXTENSIONS = [
  StarterKit.configure({
    heading: false,
    codeBlock: false,
    code: false,
    blockquote: false,
    horizontalRule: false,
  }),
  Underline,
  Link.configure({ openOnClick: false, HTMLAttributes: { class: 'underline text-primary' } }),
]

function ToolbarButton({
  onClick, active, disabled, title, children,
}: {
  onClick: () => void
  active?: boolean
  disabled?: boolean
  title: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onMouseDown={(e) => { e.preventDefault(); onClick() }}
      disabled={disabled}
      title={title}
      className={`p-1.5 rounded transition-colors ${
        active
          ? 'bg-foreground text-background'
          : 'hover:bg-muted text-foreground'
      } disabled:opacity-40 disabled:cursor-not-allowed`}
    >
      {children}
    </button>
  )
}

export default function RichTextEditor({ value, onChange, disabled }: Props) {
  const editor = useEditor({
    extensions: EXTENSIONS,
    content: value,
    editable: !disabled,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
  })

  // Sync external value changes (e.g. when dialog reopens with fresh data)
  useEffect(() => {
    if (!editor) return
    if (editor.getHTML() !== value) {
      editor.commands.setContent(value)
    }
  }, [value, editor])

  // Sync disabled state
  useEffect(() => {
    if (!editor) return
    editor.setEditable(!disabled)
  }, [disabled, editor])

  function setLink() {
    if (!editor) return
    const prev = editor.getAttributes('link').href as string | undefined
    const url = window.prompt('URL', prev ?? 'https://')
    if (url === null) return
    if (url === '') {
      editor.chain().focus().unsetLink().run()
    } else {
      editor.chain().focus().setLink({ href: url }).run()
    }
  }

  if (!editor) return null

  return (
    <div className={`border border-input rounded-md overflow-hidden ${disabled ? 'opacity-60' : ''}`}>
      {!disabled && (
        <div className="flex items-center gap-0.5 px-2 py-1.5 border-b border-input bg-muted/30 flex-wrap">
          <ToolbarButton onClick={() => editor.chain().focus().toggleBold().run()} active={editor.isActive('bold')} title="Bold">
            <Bold size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => editor.chain().focus().toggleItalic().run()} active={editor.isActive('italic')} title="Italic">
            <Italic size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => editor.chain().focus().toggleUnderline().run()} active={editor.isActive('underline')} title="Underline">
            <UnderlineIcon size={14} />
          </ToolbarButton>
          <span className="w-px h-4 bg-border mx-1" />
          <ToolbarButton onClick={setLink} active={editor.isActive('link')} title="Link">
            <LinkIcon size={14} />
          </ToolbarButton>
          <span className="w-px h-4 bg-border mx-1" />
          <ToolbarButton onClick={() => editor.chain().focus().toggleBulletList().run()} active={editor.isActive('bulletList')} title="Bullet list">
            <List size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => editor.chain().focus().toggleOrderedList().run()} active={editor.isActive('orderedList')} title="Numbered list">
            <ListOrdered size={14} />
          </ToolbarButton>
          <span className="w-px h-4 bg-border mx-1" />
          <ToolbarButton onClick={() => editor.chain().focus().setHardBreak().run()} title="Line break">
            <Minus size={14} />
          </ToolbarButton>
        </div>
      )}
      <EditorContent
        editor={editor}
        className="px-4 py-3 text-sm min-h-[220px] max-h-[400px] overflow-y-auto bg-white focus-within:outline-none [&_.ProseMirror]:outline-none [&_.ProseMirror]:min-h-[180px] [&_.ProseMirror_ul]:list-disc [&_.ProseMirror_ul]:pl-5 [&_.ProseMirror_ol]:list-decimal [&_.ProseMirror_ol]:pl-5 [&_.ProseMirror_li]:my-0.5 [&_.ProseMirror_p]:my-1 [&_.ProseMirror_a]:underline [&_.ProseMirror_a]:text-primary"
      />
    </div>
  )
}
