import * as Lucide from "lucide-react";

const { icons } = Lucide;

/** Lucide ikonunu admin'de girilen isimden çözer (eski takma adlar dahil); bilinmeyen isimde kutu ikonu. */
export default function Icon({ name, ...props }) {
  const Cmp = icons[name] ?? (/^[A-Z]/.test(name ?? "") ? Lucide[name] : null) ?? icons.Box;
  return <Cmp {...props} />;
}
