import {
  ActivityIcon,
  BellIcon,
  BookOpenIcon,
  CheckCircle2Icon,
  ChevronDownIcon,
  CircleHelpIcon,
  ClockIcon,
  CopyIcon,
  DatabaseIcon,
  FileTextIcon,
  FolderOpenIcon,
  MessageSquareIcon,
  MoreHorizontalIcon,
  PanelLeftIcon,
  PlusIcon,
  SearchIcon,
  SettingsIcon,
  ShieldCheckIcon,
  SlidersHorizontalIcon,
  SparklesIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
  UploadIcon,
  UserCircleIcon,
} from "lucide-react"

import { StatusBadge } from "@/components/common/status-badge"
import { PageContainer } from "@/components/layout/page-container"
import { PageHeader } from "@/components/layout/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const navItems = [
  { label: "New chat", icon: PlusIcon, active: false },
  { label: "Chat", icon: MessageSquareIcon, active: true },
  { label: "Documents", icon: FileTextIcon, active: false },
  { label: "Knowledge", icon: DatabaseIcon, active: false },
  { label: "Activity", icon: ActivityIcon, active: false },
  { label: "Settings", icon: SettingsIcon, active: false },
]

const metrics = [
  { label: "Total documents", value: "1,284", detail: "Across 6 knowledge bases" },
  { label: "Ready documents", value: "1,221", detail: "95% available for retrieval" },
  { label: "Processing", value: "18", detail: "Queued or indexing now" },
  { label: "Recent conversations", value: "42", detail: "Last 7 days" },
]

const documents = [
  {
    name: "Employee Handbook 2026.pdf",
    type: "PDF",
    knowledgeBase: "People Operations",
    size: "8.4 MB",
    status: "ready" as const,
    uploaded: "Today, 9:42 AM",
  },
  {
    name: "Security review checklist.docx",
    type: "DOCX",
    knowledgeBase: "Security",
    size: "312 KB",
    status: "processing" as const,
    uploaded: "Today, 8:15 AM",
  },
  {
    name: "Q3 onboarding notes.md",
    type: "Markdown",
    knowledgeBase: "Product Enablement",
    size: "74 KB",
    status: "queued" as const,
    uploaded: "Yesterday",
  },
  {
    name: "Vendor risk matrix.xlsx",
    type: "Sheet",
    knowledgeBase: "Procurement",
    size: "1.1 MB",
    status: "failed" as const,
    uploaded: "Jul 30, 2026",
  },
]

const knowledgeBases = [
  {
    name: "People Operations",
    description: "Policies, benefits, onboarding, and internal processes.",
    documents: 318,
    updated: "12 min ago",
    status: "active" as const,
  },
  {
    name: "Security",
    description: "Review checklists, access standards, and incident playbooks.",
    documents: 146,
    updated: "1 hr ago",
    status: "active" as const,
  },
  {
    name: "Product Enablement",
    description: "Release notes, positioning docs, and customer-facing guides.",
    documents: 227,
    updated: "Yesterday",
    status: "active" as const,
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r bg-card lg:block">
          <div className="sticky top-0 flex h-screen flex-col">
            <div className="flex h-14 items-center gap-2 border-b px-4">
              <div className="flex size-8 items-center justify-center rounded-md border bg-primary text-primary-foreground">
                <BookOpenIcon className="size-4" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-semibold">Knowledge Assistant</p>
                <p className="text-xs text-muted-foreground">Internal workspace</p>
              </div>
            </div>

            <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Primary">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href="#"
                  className={
                    item.active
                      ? "flex h-9 items-center gap-2 rounded-md bg-primary/10 px-3 text-sm font-medium text-primary"
                      : "flex h-9 items-center gap-2 rounded-md px-3 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                  }
                >
                  <item.icon className="size-4" aria-hidden="true" />
                  {item.label}
                </a>
              ))}
            </nav>

            <div className="border-t p-4">
              <div className="rounded-lg border bg-background p-3">
                <div className="flex items-center gap-2">
                  <ShieldCheckIcon className="size-4 text-primary" aria-hidden="true" />
                  <p className="text-sm font-medium">Citations required</p>
                </div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  Answers show source documents before they can be shared.
                </p>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/95 px-4 sm:px-6 lg:px-8">
            <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation">
              <PanelLeftIcon aria-hidden="true" />
            </Button>
            <button className="hidden h-8 items-center gap-2 rounded-md border px-2.5 text-sm font-medium lg:flex">
              Acme Operations
              <ChevronDownIcon className="size-4 text-muted-foreground" aria-hidden="true" />
            </button>
            <div className="relative max-w-md flex-1">
              <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input aria-label="Global search" className="pl-8" placeholder="Search documents, answers, or conversations" />
            </div>
            <Button variant="ghost" size="icon" aria-label="Help">
              <CircleHelpIcon aria-hidden="true" />
            </Button>
            <Button variant="ghost" size="icon" aria-label="Notifications">
              <BellIcon aria-hidden="true" />
            </Button>
            <Button variant="ghost" size="icon" aria-label="Profile">
              <UserCircleIcon aria-hidden="true" />
            </Button>
          </header>

          <PageContainer size="wide">
            <PageHeader
              title="Knowledge workspace"
              description="Ask grounded questions, monitor document readiness, and manage the knowledge bases that power retrieval."
              actions={
                <>
                  <Button variant="outline">
                    <UploadIcon aria-hidden="true" />
                    Upload
                  </Button>
                  <Button>
                    <PlusIcon aria-hidden="true" />
                    New chat
                  </Button>
                </>
              }
            />

            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Operational summary">
              {metrics.map((metric) => (
                <Card key={metric.label} className="rounded-lg shadow-none">
                  <CardHeader className="pb-0">
                    <CardTitle className="text-sm">{metric.label}</CardTitle>
                    <CardDescription>{metric.detail}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-semibold tracking-tight">{metric.value}</p>
                  </CardContent>
                </Card>
              ))}
            </section>

            <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
              <div className="space-y-6">
                <Card className="rounded-lg shadow-none">
                  <CardHeader className="border-b pb-4">
                    <CardTitle>Recent documents</CardTitle>
                    <CardDescription>Search, filter, and review processing status.</CardDescription>
                    <CardAction>
                      <Button variant="outline" size="sm">
                        <SlidersHorizontalIcon aria-hidden="true" />
                        Status
                      </Button>
                    </CardAction>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="mb-4 flex flex-col gap-3 sm:flex-row">
                      <div className="relative flex-1">
                        <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                        <Input className="pl-8" aria-label="Search documents" placeholder="Search documents" />
                      </div>
                      <Button variant="outline">
                        <UploadIcon aria-hidden="true" />
                        Upload files
                      </Button>
                    </div>

                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Knowledge base</TableHead>
                          <TableHead>Size</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Uploaded</TableHead>
                          <TableHead className="w-10">
                            <span className="sr-only">Actions</span>
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {documents.map((document) => (
                          <TableRow key={document.name}>
                            <TableCell className="font-medium">{document.name}</TableCell>
                            <TableCell>{document.type}</TableCell>
                            <TableCell>{document.knowledgeBase}</TableCell>
                            <TableCell>{document.size}</TableCell>
                            <TableCell>
                              <StatusBadge status={document.status}>{document.status}</StatusBadge>
                            </TableCell>
                            <TableCell className="text-muted-foreground">{document.uploaded}</TableCell>
                            <TableCell>
                              <Button variant="ghost" size="icon-sm" aria-label={`Open actions for ${document.name}`}>
                                <MoreHorizontalIcon aria-hidden="true" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>

                <div className="grid gap-4 lg:grid-cols-3">
                  {knowledgeBases.map((knowledgeBase) => (
                    <Card key={knowledgeBase.name} className="rounded-lg shadow-none">
                      <CardHeader>
                        <CardTitle>{knowledgeBase.name}</CardTitle>
                        <CardDescription>{knowledgeBase.description}</CardDescription>
                        <CardAction>
                          <Button variant="ghost" size="icon-sm" aria-label={`More actions for ${knowledgeBase.name}`}>
                            <MoreHorizontalIcon aria-hidden="true" />
                          </Button>
                        </CardAction>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Documents</span>
                          <span className="font-medium">{knowledgeBase.documents}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Last updated</span>
                          <span className="font-medium">{knowledgeBase.updated}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <StatusBadge status={knowledgeBase.status}>Active</StatusBadge>
                          <Button variant="outline" size="sm">
                            <FolderOpenIcon aria-hidden="true" />
                            Open
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <aside className="space-y-6">
                <Card className="rounded-lg shadow-none">
                  <CardHeader className="border-b pb-4">
                    <CardTitle>Current answer</CardTitle>
                    <CardDescription>Document-style response with feedback controls.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-4">
                    <div className="rounded-lg border bg-muted/30 p-4">
                      <div className="mb-3 flex items-center gap-2">
                        <SparklesIcon className="size-4 text-primary" aria-hidden="true" />
                        <p className="text-sm font-medium">Assistant</p>
                        <Badge variant="outline" className="ml-auto">4 sources</Badge>
                      </div>
                      <p className="text-sm leading-6">
                        The latest onboarding guidance requires completing identity verification,
                        security awareness training, and manager-approved system access before the
                        employee&apos;s first production login.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm"><CopyIcon aria-hidden="true" />Copy</Button>
                      <Button variant="outline" size="sm"><ThumbsUpIcon aria-hidden="true" />Helpful</Button>
                      <Button variant="outline" size="sm"><ThumbsDownIcon aria-hidden="true" />Not helpful</Button>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-lg shadow-none">
                  <CardHeader>
                    <CardTitle>Sources</CardTitle>
                    <CardDescription>Cited evidence for the selected answer.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {["Employee Handbook 2026.pdf", "Security review checklist.docx", "Manager onboarding playbook.pdf"].map((source, index) => (
                      <div key={source} className="rounded-lg border p-3">
                        <div className="flex items-start gap-2">
                          <FileTextIcon className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
                          <div>
                            <p className="text-sm font-medium">{source}</p>
                            <p className="text-xs text-muted-foreground">Page {index + 3} · People Operations</p>
                          </div>
                        </div>
                        <p className="mt-2 text-xs leading-5 text-muted-foreground">
                          Relevant excerpt matched identity verification and access prerequisites.
                        </p>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className="rounded-lg shadow-none">
                  <CardHeader>
                    <CardTitle>Retrieval settings</CardTitle>
                    <CardDescription>Visible controls for review and tuning.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <SettingRow label="Results" value="8" />
                    <SettingRow label="Similarity threshold" value="0.78" />
                    <SettingRow label="Reranking" value="Enabled" />
                    <SettingRow label="Chunk size" value="900 tokens" />
                  </CardContent>
                </Card>
              </aside>
            </section>

            <section className="grid gap-4 lg:grid-cols-3">
              <Card className="rounded-lg shadow-none lg:col-span-2">
                <CardHeader>
                  <CardTitle>Recent conversations</CardTitle>
                  <CardDescription>Operational questions answered from indexed sources.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {["What access is required for new engineers?", "Summarize vendor security exceptions", "Which policies changed this quarter?"].map((conversation) => (
                    <div key={conversation} className="flex items-center gap-3 rounded-lg border p-3">
                      <MessageSquareIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                      <p className="flex-1 text-sm font-medium">{conversation}</p>
                      <ClockIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                      <span className="text-xs text-muted-foreground">Today</span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="rounded-lg shadow-none">
                <CardHeader>
                  <CardTitle>Upload progress</CardTitle>
                  <CardDescription>Processing state for recent files.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ProgressRow label="Parsing" value="Complete" percent="100%" />
                  <ProgressRow label="Chunking" value="In progress" percent="68%" />
                  <ProgressRow label="Embedding" value="Queued" percent="0%" />
                  <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                    <CheckCircle2Icon className="size-4" aria-hidden="true" />
                    12 documents are ready for chat.
                  </div>
                </CardContent>
              </Card>
            </section>
          </PageContainer>
        </div>
      </div>
    </div>
  )
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border p-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function ProgressRow({
  label,
  value,
  percent,
}: {
  label: string
  value: string
  percent: string
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">{value}</span>
      </div>
      <div className="h-2 rounded-sm bg-muted">
        <div className="h-2 rounded-sm bg-primary" style={{ width: percent }} />
      </div>
    </div>
  )
}
