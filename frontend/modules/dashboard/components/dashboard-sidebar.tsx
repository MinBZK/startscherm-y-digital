"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  Home,
  Folder,
  CheckSquare,
  Calendar,
  Book,
  Users,
  Monitor,
  Search,
  MessageSquare,
  Mail,
  Bot,
} from "lucide-react";
import { useState } from "react";
import { SidebarItem } from "@/app/sidebar-item";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { SearchDialogContent } from "@/app/dashboard/components/search-dialog-content";
// import { AssistentDialogContent } from "@/app/dashboard/components/assistent-dialog-content";
import { DossierItem } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/store/sidebar-store";

export function Sidebar({ dossiers }: { dossiers: DossierItem[] }) {
  const pathname = usePathname();
  const [hasSearched, setHasSearched] = useState(false);
  const {
    clearLegalData,
    closeChat,
    closeSidebar,
    setMessages,
    setText,
    setValidationText,
    setDossierId,
  } = useSidebarStore();

  const handleOpenChange = () => {
    setHasSearched(false);
  };

  const handleNewChat = (open: boolean) => {
    if (!open) {
      closeChat();
      setMessages([]);
      setText("");
      setValidationText("");
      setDossierId("");
      clearLegalData();
      closeSidebar();
    }
  };

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="p-4 pt-0 border-b border-gray-200 flex items-center justify-center">
        <Image
          className="object-contain"
          src="/beeldmerk.svg"
          alt="Logo Rijksoverheid"
          width={30}
          height={60}
        />
      </div>

      <div className="p-2">
        <Dialog onOpenChange={handleOpenChange}>
          <DialogTrigger asChild>
            <div className="relative w-full cursor-pointer">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <Search className="h-4 w-4 text-lintblauw" />
              </div>
              <input
                type="search"
                placeholder="Zoeken"
                className="pl-10 w-full text-sm border border-lintblauw placeholder:text-lintblauw text-lintblauw focus-visible:outline-none rounded-md py-1.5 px-3"
                readOnly
              />
            </div>
          </DialogTrigger>
          <DialogContent
            id="search-dialog-content"
            className={cn(
              "p-0 w-[90vw] bg-gray-50 max-w-none focus:outline-none",
              !hasSearched ? "h-[60vh]" : "h-[90vh]"
            )}
          >
            <DialogTitle className="sr-only">Zoek en vind</DialogTitle>
            <div className="flex flex-col">
              <div className="flex items-center justify-center">
                <Image
                  className="object-contain"
                  src="/beeldmerk.svg"
                  alt="Logo Rijksoverheid"
                  width={30}
                  height={60}
                />
              </div>
              <div className="">
                <SearchDialogContent
                  dossiers={dossiers}
                  hasSearched={hasSearched}
                  setHasSearched={setHasSearched}
                />
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        <ul className="space-y-1">
          <li>
            <SidebarItem
              icon={<Home className="size-5 text-lintblauw" />}
              text="Mijn dag"
              textColor="text-black"
              active={pathname === "/"}
              href="/"
            />
          </li>
          <li>
            <SidebarItem
              icon={<Folder className="size-5 text-gray-700" />}
              text="Dossiers"
              textColor="text-gray-700"
            />
          </li>
          <li>
            <SidebarItem
              icon={<CheckSquare className="size-5 text-gray-700" />}
              text="Taken"
              textColor="text-gray-700"
            />
          </li>
          <li>
            <SidebarItem
              icon={<Calendar className="size-5 text-gray-700" />}
              text="Agenda"
              textColor="text-gray-700"
            />
          </li>
        </ul>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <ul className="space-y-1">
            <li>
              <SidebarItem
                icon={<Book className="size-5 text-lintblauw" />}
                text="Rijksadresgids"
                textColor="text-lintblauw"
              />
            </li>
            <li>
              <SidebarItem
                icon={<Book className="size-5 text-lintblauw" />}
                text="Kenniscentrum"
                textColor="text-lintblauw"
              />
            </li>
            <li>
              <SidebarItem
                icon={<Users className="size-5 text-lintblauw" />}
                text="Organisaties"
                textColor="text-lintblauw"
              />
            </li>
            <li>
              <SidebarItem
                icon={<Monitor className="size-5 text-lintblauw" />}
                text="Selfserviceportal SSC-ICT"
                textColor="text-lintblauw"
              />
            </li>
          </ul>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center px-3 mb-2">
            <h3 className="text-sm font-semibold text-gray-500 flex-1">
              Mijn favoriete apps
            </h3>
            <span className="text-white bg-gray-400 cursor-pointer text-lg rounded-full w-4 h-4 flex items-center justify-center font-bold">
              +
            </span>
          </div>
          <ul className="">
            {/* <li>
              <SidebarItem
                icon={
                  <svg
                    width="18"
                    height="19"
                    viewBox="0 0 18 19"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M18 8.17285C18 8.94043 17.9971 9.70508 17.9912 10.4668C17.9912 11.2227 17.9912 11.9844 17.9912 12.752C17.9912 13.1738 17.9092 13.5723 17.7451 13.9473C17.5869 14.3223 17.3701 14.6475 17.0947 14.9229C16.8193 15.1982 16.4941 15.418 16.1191 15.582C15.7441 15.7402 15.3457 15.8193 14.9238 15.8193C14.6309 15.8193 14.3525 15.7812 14.0889 15.7051C13.8721 16.1328 13.6025 16.5195 13.2803 16.8652C12.9639 17.2109 12.6094 17.5039 12.2168 17.7441C11.8301 17.9844 11.4111 18.1719 10.96 18.3066C10.5088 18.4355 10.043 18.5 9.5625 18.5C9.02344 18.5 8.50488 18.4209 8.00684 18.2627C7.51465 18.0986 7.05762 17.8701 6.63574 17.5771C6.21973 17.2783 5.85059 16.9209 5.52832 16.5049C5.21191 16.0889 4.96582 15.6289 4.79004 15.125H1.125C0.972656 15.125 0.826172 15.0957 0.685547 15.0371C0.550781 14.9785 0.430664 14.8994 0.325195 14.7998C0.225586 14.6943 0.146484 14.5742 0.0878906 14.4395C0.0292969 14.2988 0 14.1523 0 14V5C0 4.84766 0.0292969 4.7041 0.0878906 4.56934C0.146484 4.42871 0.225586 4.30859 0.325195 4.20898C0.430664 4.10352 0.550781 4.02148 0.685547 3.96289C0.826172 3.9043 0.972656 3.875 1.125 3.875H6.75C6.75 3.41211 6.83789 2.97559 7.01367 2.56543C7.18945 2.15527 7.42969 1.79785 7.73438 1.49316C8.04492 1.18262 8.40234 0.939453 8.80664 0.763672C9.2168 0.587891 9.65625 0.5 10.125 0.5C10.5879 0.5 11.0244 0.587891 11.4346 0.763672C11.8447 0.939453 12.2021 1.18262 12.5068 1.49316C12.8174 1.79785 13.0605 2.15527 13.2363 2.56543C13.4121 2.97559 13.5 3.41211 13.5 3.875C13.5 4.23242 13.4443 4.57812 13.333 4.91211C13.2275 5.24023 13.0752 5.54492 12.876 5.82617C12.6826 6.10156 12.4453 6.34766 12.1641 6.56445C11.8887 6.77539 11.584 6.93945 11.25 7.05664V7.25H17.0771C17.2061 7.25 17.3262 7.27637 17.4375 7.3291C17.5488 7.37598 17.6455 7.44043 17.7275 7.52246C17.8096 7.60449 17.874 7.70117 17.9209 7.8125C17.9736 7.92383 18 8.04395 18 8.17285ZM10.125 1.625C9.81445 1.625 9.52148 1.68359 9.24609 1.80078C8.97656 1.91797 8.73926 2.0791 8.53418 2.28418C8.3291 2.48926 8.16797 2.72949 8.05078 3.00488C7.93359 3.27441 7.875 3.56445 7.875 3.875H10.125C10.2773 3.875 10.4209 3.9043 10.5557 3.96289C10.6963 4.02148 10.8164 4.10352 10.916 4.20898C11.0215 4.30859 11.1035 4.42871 11.1621 4.56934C11.2207 4.7041 11.25 4.84766 11.25 5V5.82617C11.6016 5.62109 11.877 5.3457 12.0762 5C12.2754 4.6543 12.375 4.2793 12.375 3.875C12.375 3.56445 12.3164 3.27441 12.1992 3.00488C12.082 2.72949 11.9209 2.48926 11.7158 2.28418C11.5107 2.0791 11.2705 1.91797 10.9951 1.80078C10.7256 1.68359 10.4355 1.625 10.125 1.625ZM5.34375 13.1562H7.03125V7.53125H9.28125V5.84375H3.09375V7.53125H5.34375V13.1562ZM13.5 13.4375V8.375H11.25V14C11.25 14.1523 11.2207 14.2988 11.1621 14.4395C11.1035 14.5742 11.0215 14.6943 10.916 14.7998C10.8164 14.8994 10.6963 14.9785 10.5557 15.0371C10.4209 15.0957 10.2773 15.125 10.125 15.125H6.00293C6.16699 15.4707 6.37207 15.7812 6.61816 16.0566C6.87012 16.332 7.15137 16.5693 7.46191 16.7686C7.77246 16.9619 8.10352 17.1113 8.45508 17.2168C8.8125 17.3223 9.18164 17.375 9.5625 17.375C10.1074 17.375 10.6172 17.2725 11.0918 17.0674C11.5723 16.8564 11.9883 16.5752 12.3398 16.2236C12.6973 15.8662 12.9785 15.4502 13.1836 14.9756C13.3945 14.4951 13.5 13.9824 13.5 13.4375ZM16.875 12.752V8.375H14.625V13.4375C14.625 13.8359 14.5752 14.2402 14.4756 14.6504C14.6396 14.6797 14.7891 14.6943 14.9238 14.6943C15.1934 14.6943 15.4453 14.6445 15.6797 14.5449C15.9199 14.4395 16.1279 14.2988 16.3037 14.123C16.4795 13.9473 16.6172 13.7422 16.7168 13.5078C16.8223 13.2734 16.875 13.0215 16.875 12.752ZM15.75 6.125C15.4395 6.125 15.1465 6.06641 14.8711 5.94922C14.6016 5.83203 14.3643 5.6709 14.1592 5.46582C13.9541 5.26074 13.793 5.02344 13.6758 4.75391C13.5586 4.47852 13.5 4.18555 13.5 3.875C13.5 3.56445 13.5586 3.27441 13.6758 3.00488C13.793 2.72949 13.9541 2.48926 14.1592 2.28418C14.3643 2.0791 14.6016 1.91797 14.8711 1.80078C15.1465 1.68359 15.4395 1.625 15.75 1.625C16.0605 1.625 16.3506 1.68359 16.6201 1.80078C16.8955 1.91797 17.1357 2.0791 17.3408 2.28418C17.5459 2.48926 17.707 2.72949 17.8242 3.00488C17.9414 3.27441 18 3.56445 18 3.875C18 4.18555 17.9414 4.47852 17.8242 4.75391C17.707 5.02344 17.5459 5.26074 17.3408 5.46582C17.1357 5.6709 16.8955 5.83203 16.6201 5.94922C16.3506 6.06641 16.0605 6.125 15.75 6.125ZM15.75 2.75C15.5918 2.75 15.4453 2.7793 15.3105 2.83789C15.1758 2.89648 15.0557 2.97852 14.9502 3.08398C14.8506 3.18359 14.7715 3.30078 14.7129 3.43555C14.6543 3.57031 14.625 3.7168 14.625 3.875C14.625 4.0332 14.6543 4.17969 14.7129 4.31445C14.7715 4.44922 14.8506 4.56934 14.9502 4.6748C15.0557 4.77441 15.1758 4.85352 15.3105 4.91211C15.4453 4.9707 15.5918 5 15.75 5C15.9082 5 16.0547 4.9707 16.1895 4.91211C16.3242 4.85352 16.4414 4.77441 16.541 4.6748C16.6465 4.56934 16.7285 4.44922 16.7871 4.31445C16.8457 4.17969 16.875 4.0332 16.875 3.875C16.875 3.7168 16.8457 3.57031 16.7871 3.43555C16.7285 3.30078 16.6465 3.18359 16.541 3.08398C16.4414 2.97852 16.3242 2.89648 16.1895 2.83789C16.0547 2.7793 15.9082 2.75 15.75 2.75Z"
                      fill="#1A1A1A"
                    />
                  </svg>
                }
                text="Microsoft Teams"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
              />
            </li> */}
            {/* <li>
              <Dialog onOpenChange={(open) => handleNewChat(open)}>
                <DialogTrigger asChild>
                  <button className="flex items-center px-2 py-2 text-sm rounded-md transition-colors text-gray-700 font-normal hover:bg-gray-100 w-full text-left">
                    <span className="mr-3 flex items-center justify-center bg-gray-100 rounded-lg w-9 h-9">
                      <Bot className="size-5 text-gray-700" />
                    </span>
                    <span>Juridische assistent</span>
                  </button>
                </DialogTrigger>
                <DialogContent className="p-0 w-[90vw] h-[90vh] bg-gray-50 max-w-none">
                  <DialogTitle className="sr-only">
                    Juridische assistent
                  </DialogTitle>
                  <AssistentDialogContent />
                </DialogContent>
              </Dialog>
            </li> */}
            <li>
              <SidebarItem
                icon={
                  <Bot
                    className={`size-5 ${
                      pathname === "/digitale-assistent"
                        ? "text-lintblauw"
                        : "text-gray-700"
                    }`}
                  />
                }
                text="Digitale assistent"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
                href="/digitale-assistent"
                active={pathname === "/digitale-assistent"}
                bgColor={
                  pathname === "/digitale-assistent" ? "bg-[#F2F7FA]" : ""
                }
                textColor={
                  pathname === "/digitale-assistent"
                    ? "text-black"
                    : "text-gray-700"
                }
              />
            </li>
            <li>
              <SidebarItem
                icon={<Search className="size-5 text-gray-700" />}
                text="Zoek en vind"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
              />
            </li>
            <li>
              <SidebarItem
                icon={
                  <svg
                    width="18"
                    height="19"
                    viewBox="0 0 18 19"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M16.875 0.5C17.0273 0.5 17.1709 0.529297 17.3057 0.587891C17.4463 0.646484 17.5664 0.728516 17.666 0.833984C17.7715 0.933594 17.8535 1.05371 17.9121 1.19434C17.9707 1.3291 18 1.47266 18 1.625V17.375C18 17.5273 17.9707 17.6738 17.9121 17.8145C17.8535 17.9492 17.7715 18.0693 17.666 18.1748C17.5664 18.2744 17.4463 18.3535 17.3057 18.4121C17.1709 18.4707 17.0273 18.5 16.875 18.5H4.5C4.34766 18.5 4.20117 18.4707 4.06055 18.4121C3.92578 18.3535 3.80566 18.2744 3.7002 18.1748C3.60059 18.0693 3.52148 17.9492 3.46289 17.8145C3.4043 17.6738 3.375 17.5273 3.375 17.375V15.125H1.125C0.972656 15.125 0.826172 15.0957 0.685547 15.0371C0.550781 14.9785 0.430664 14.8994 0.325195 14.7998C0.225586 14.6943 0.146484 14.5742 0.0878906 14.4395C0.0292969 14.2988 0 14.1523 0 14V5C0 4.84766 0.0292969 4.7041 0.0878906 4.56934C0.146484 4.42871 0.225586 4.30859 0.325195 4.20898C0.430664 4.10352 0.550781 4.02148 0.685547 3.96289C0.826172 3.9043 0.972656 3.875 1.125 3.875H3.375V1.625C3.375 1.47266 3.4043 1.3291 3.46289 1.19434C3.52148 1.05371 3.60059 0.933594 3.7002 0.833984C3.80566 0.728516 3.92578 0.646484 4.06055 0.587891C4.20117 0.529297 4.34766 0.5 4.5 0.5H16.875ZM16.875 17.375V14H11.25C11.25 14.1523 11.2207 14.2988 11.1621 14.4395C11.1035 14.5742 11.0215 14.6943 10.916 14.7998C10.8164 14.8994 10.6963 14.9785 10.5557 15.0371C10.4209 15.0957 10.2773 15.125 10.125 15.125H4.5V17.375H16.875ZM16.875 12.875V9.5H11.25V12.875H16.875ZM16.875 8.375V5H11.25V8.375H16.875ZM16.875 3.875V1.625H4.5V3.875H16.875ZM6.56543 13.1562H8.42871L10.0459 5.84375H8.25293L7.48828 10.0186L6.53027 5.84375H4.75488L3.84082 10.0449L3.01465 5.84375H1.2041L2.83008 13.1562H4.71973L5.61621 8.95508L6.56543 13.1562Z"
                      fill="#1A1A1A"
                    />
                  </svg>
                }
                text="Word"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
              />
            </li>
            <li>
              <SidebarItem
                icon={<MessageSquare className="size-5 text-gray-700" />}
                text="Chat"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
              />
            </li>
            <li>
              <SidebarItem
                icon={<Mail className="size-5 text-gray-700" />}
                text="Mail"
                iconBg="bg-gray-100 rounded-lg w-9 h-9"
              />
            </li>
          </ul>
          <div className="mt-4 px-3">
            <Link href="#" className="flex items-center text-xs text-gray-400">
              <span>Alle apps</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="ml-1"
              >
                <path d="M5 12h14" />
                <path d="m12 5 7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </nav>
    </aside>
  );
}
