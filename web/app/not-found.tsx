import Link from "next/link";
import { Panel } from "@/components/ui/panel";
import { IconEmpty } from "@/components/ui/icons";

export default function NotFound() {
  return (
    <Panel className="mx-auto mt-10 max-w-xl px-6 py-16 text-center">
      <IconEmpty className="mx-auto size-7 text-muted-foreground" />
      <h1 className="editorial mt-6 text-[27px]">Halaman tidak ditemukan</h1>
      <p className="mx-auto mt-3 max-w-sm text-[13px] leading-[1.65] text-muted-foreground">Route itu tidak ada, atau tickernya tidak dilayani sumber yang sedang aktif.</p>
      <Link href="/" className="mt-8 inline-flex min-h-11 items-center justify-center rounded-[6px] bg-primary px-5 text-[13px] font-medium text-primary-foreground transition-[background-color,transform] duration-200 hover:bg-primary/88 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
        Kembali ke Today
      </Link>
    </Panel>
  );
}
