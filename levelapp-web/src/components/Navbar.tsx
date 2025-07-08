import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="sticky max-w-screen-2xl mx-auto top-0 z-50 bg-gradient-to-b from-transparent to-black/20 backdrop-blur-md  py-4 flex items-center justify-between px-4 md:px-20">
      <div className="flex items-center ">
        <img src="/assets/logo-black.svg" alt="Logo" className="h-8" />
      </div>
      <div className="flex items-center gap-4 ">
        <Link
          href="/signin "
          target="_blank"
          className="text-white text-sm nav-link transition"
        >
          Sign In
        </Link>
        <Link
          href="https://norma.dev"
          target="_blank"
          className="text-white text-sm nav-link transition"
        >
          Norma.dev
        </Link>
      </div>
    </nav>
  );
}
