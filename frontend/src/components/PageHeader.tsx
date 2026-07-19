export function PageHeader() {
  return (
    <div className="flex items-center gap-2.5 mb-9">
      <div aria-hidden="true" className="relative size-[26px] shrink-0 rounded-[3px] border-2 border-ink">
        <div className="absolute left-1.5 top-1.5 h-3 w-2.5 border-r-2 border-ink" />
      </div>
      <div className="font-heading text-[17px] font-bold tracking-wide">RealDoor</div>
    </div>
  );
}
