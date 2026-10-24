import { icons } from "lucide-react";

/** Lucide ikonunu admin'de girilen isimden çözer; bilinmeyen isimde kutu ikonu. */
export default function Icon({ name, ...props }) {
  const Cmp = icons[name] ?? icons.Box;
  return <Cmp {...props} />;
}
