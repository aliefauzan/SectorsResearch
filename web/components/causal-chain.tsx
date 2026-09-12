"use client";

import { useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import type { CausalGraph, CausalNode, ImpactDirection } from "@/lib/types";
import { CitationDialog } from "@/components/citation-dialog";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  IconCompanies,
  IconDocument,
  IconGauge,
  IconGraph,
  IconPolicy,
  IconSource,
  IconWeather,
} from "@/components/ui/icons";

type ChainNodeData = { causal: CausalNode; onSelect: (id: string) => void };
type ChainFlowNode = Node<ChainNodeData, "chain">;

const sourceIcons = {
  weather: IconWeather,
  macro: IconPolicy,
  commodity: IconGauge,
  filing: IconDocument,
  sectors: IconSource,
  policy: IconPolicy,
  market: IconSource,
  financial: IconDocument,
};

const kindLabels: Record<CausalNode["kind"], string> = {
  source: "Sumber",
  mechanism: "Mekanisme",
  company: "Emiten",
  observation: "Observasi",
};

function ChainNode({ data }: NodeProps<ChainFlowNode>) {
  const node = data.causal;
  const Icon = node.kind === "company" ? IconCompanies : node.kind === "mechanism" ? IconGraph : sourceIcons[node.sourceType ?? "market"];
  return (
    <div className={`w-[214px] rounded-[10px] border bg-surface ${node.kind === "company" ? "border-foreground" : "border-border"}`}>
      {node.kind !== "source" ? <Handle type="target" position={Position.Left} className="!size-1.5 !border-0 !bg-[var(--muted-foreground)]" /> : null}
      <button
        type="button"
        onClick={() => data.onSelect(node.id)}
        className="w-full cursor-pointer rounded-[inherit] px-3.5 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
      >
        <span className="flex items-center gap-2">
          <Icon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="meta text-muted-foreground">{kindLabels[node.kind]}</span>
        </span>
        <span className="mt-2 line-clamp-3 block text-[12px] font-medium leading-[1.5]">{node.label}</span>
        {node.relevance ? <span className="mt-2 block font-mono text-[10px] tabular-nums text-muted-foreground">relevansi {node.relevance}/100</span> : null}
      </button>
      {node.kind !== "observation" ? <Handle type="source" position={Position.Right} className="!size-1.5 !border-0 !bg-[var(--muted-foreground)]" /> : null}
    </div>
  );
}

const nodeTypes = { chain: ChainNode };

/* Edge hues sit between the light and dark palettes so one value reads on
   bone and on ink. Non-text, so they are held to the same restraint as the
   pastels rather than to a contrast ratio. */
const edgeColor: Record<ImpactDirection, string> = {
  Supported: "#5e8f63",
  Adverse: "#c0645f",
  Mixed: "#b08a3e",
  Unrelated: "#8c8880",
  Unverified: "#8c8880",
};

export function CausalChain({ graph }: { graph: CausalGraph }) {
  const [selectedId, setSelectedId] = useState(`company-${graph.targetSymbol}`);
  const selected = graph.nodes.find((node) => node.id === selectedId) ?? graph.nodes[0];
  const { nodes, edges } = useMemo(() => {
    const groups = {
      source: graph.nodes.filter((node) => node.kind === "source"),
      mechanism: graph.nodes.filter((node) => node.kind === "mechanism"),
      company: graph.nodes.filter((node) => node.kind === "company"),
      observation: graph.nodes.filter((node) => node.kind === "observation"),
    };
    const x = { source: 0, mechanism: 296, company: 596, observation: 896 };
    const maxRows = Math.max(groups.source.length, groups.observation.length, 1);
    const flowNodes: ChainFlowNode[] = (Object.keys(groups) as Array<keyof typeof groups>).flatMap((kind) => groups[kind].map((node, index) => {
      const rowCount = groups[kind].length;
      const centeredY = (index + (maxRows - rowCount) / 2) * 132;
      return {
        id: node.id,
        type: "chain" as const,
        position: { x: x[kind], y: centeredY },
        data: { causal: node, onSelect: setSelectedId },
        draggable: false,
        connectable: false,
        focusable: false,
        ariaLabel: `${node.kind}: ${node.label}`,
      };
    }));
    const flowEdges: Edge[] = graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      type: "smoothstep",
      label: edge.label === "observed" ? "bukti" : `${edge.direction} · ${edge.relevance}`,
      markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor[edge.direction], width: 14, height: 14 },
      style: { stroke: edgeColor[edge.direction], strokeWidth: edge.relevance >= 85 ? 2 : 1.25, opacity: 0.8 },
      labelStyle: { fill: "var(--muted-foreground)", fontSize: 9, fontFamily: "var(--font-mono)", letterSpacing: "0.05em" },
      labelBgStyle: { fill: "var(--background)", fillOpacity: 0.94 },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 3,
    }));
    return { nodes: flowNodes, edges: flowEdges };
  }, [graph]);

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-surface">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border px-5 py-3.5">
        <span className="meta text-muted-foreground">Klik node untuk memeriksa</span>
        <span aria-hidden="true" className="hidden h-3 w-px bg-border sm:block" />
        <span className="meta flex items-center gap-2 text-muted-foreground">
          Sumber <span aria-hidden="true" className="opacity-45">→</span>
          Mekanisme <span aria-hidden="true" className="opacity-45">→</span>
          Emiten <span aria-hidden="true" className="opacity-45">→</span>
          Observasi 4 pilar
        </span>
      </div>

      <div className="h-[540px] w-full bg-background" aria-label={`Causal chain ${graph.targetSymbol}`}>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.16 }} minZoom={0.38} maxZoom={1.5} nodesDraggable={false} nodesConnectable={false} onNodeClick={(_, node) => setSelectedId(node.id)}>
          <Background gap={22} size={1} color="var(--chart-grid)" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      <section className="border-t border-border px-5 py-5" aria-live="polite" aria-labelledby="selected-chain-node">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="meta text-muted-foreground">Node terpilih · {kindLabels[selected.kind]}</span>
              {selected.direction ? <StatusBadge status={selected.direction} /> : null}
            </div>
            <h3 id="selected-chain-node" className="editorial mt-2.5 text-[19px]">{selected.label}</h3>
            <p className="mt-2 max-w-3xl text-[13px] leading-[1.65] text-muted-foreground">{selected.detail}</p>
          </div>
          <div className="shrink-0"><CitationDialog citations={selected.citations} label="Bukti node" /></div>
        </div>
      </section>

      <details className="group border-t border-border">
        <summary className="flex min-h-11 cursor-pointer list-none items-center px-5 text-[12px] font-medium transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
          Buka daftar hubungan aksesibel
          <span aria-hidden="true" className="ml-auto font-mono text-[15px] leading-none text-muted-foreground">
            <span className="group-open:hidden">+</span>
            <span className="hidden group-open:inline">−</span>
          </span>
        </summary>
        <div className="overflow-x-auto border-t border-border">
          <table className="w-full min-w-[620px] text-left text-[12px]">
            <thead>
              <tr className="border-b border-border">
                <th className="meta px-5 py-2.5 font-normal text-muted-foreground">Dari</th>
                <th className="meta px-4 py-2.5 font-normal text-muted-foreground">Ke</th>
                <th className="meta px-4 py-2.5 font-normal text-muted-foreground">Arah</th>
                <th className="meta px-5 py-2.5 font-normal text-muted-foreground">Relevansi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {graph.edges.map((edge) => (
                <tr key={edge.id}>
                  <td className="px-5 py-3">{graph.nodes.find((node) => node.id === edge.from)?.label}</td>
                  <td className="px-4 py-3">{graph.nodes.find((node) => node.id === edge.to)?.label}</td>
                  <td className="px-4 py-3"><StatusBadge status={edge.direction} /></td>
                  <td className="px-5 py-3 font-mono tabular-nums">{edge.relevance}/100</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
