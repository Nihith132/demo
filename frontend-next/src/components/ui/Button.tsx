import Link from "next/link";
import type { ComponentProps } from "react";

type Variant = "primary" | "secondary";

type LinkHref = ComponentProps<typeof Link>["href"];

const base =
  "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-white/20";

const variants: Record<Variant, string> = {
  primary: "bg-white text-black hover:bg-white/90",
  secondary: "bg-white/10 text-white hover:bg-white/15 border border-white/10"
};

export function Button({
  children,
  variant = "primary",
  type = "button",
  disabled,
  onClick
}: {
  children: React.ReactNode;
  variant?: Variant;
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${base} ${variants[variant]} ${disabled ? "opacity-60" : ""}`}
    >
      {children}
    </button>
  );
}

export function ButtonLink({
  href,
  children,
  variant = "primary"
}: {
  href: LinkHref;
  children: React.ReactNode;
  variant?: Variant;
}) {
  return (
    <Link className={`${base} ${variants[variant]}`} href={href}>
      {children}
    </Link>
  );
}
