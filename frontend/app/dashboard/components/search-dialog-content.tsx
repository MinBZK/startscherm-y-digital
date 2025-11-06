"use client";

import React from "react";

import { useState } from "react";
import {
  Search,
  Mic,
  ChevronDown,
  FolderPlus,
  Share2,
  Flag,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { useDashboardSearch } from "@/modules/dashboard/hooks/use-dashboard-search";
import { useSearchStore } from "@/store/search-store";
import { SearchResultHit, DossierItem } from "@/lib/types";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { formatBucketValue } from "@/lib/utils";

// const SOURCE_TABS = [
//   "Alles",
//   "Dossiers",
//   "Helpdesk",
//   "Nieuws",
//   "HR",
//   "Wetten.nl",
//   "Chat",
//   "Ibaps",
//   "Email",
//   "Video",
//   "Archief",
// ];

const AGGREGATION_LABELS: Record<string, string> = {
  "agg-author": "Author",
  "agg-datetime_published": "Datetime published",
  "agg-filetype": "Filetype",
  "agg-created_date": "Created date",
  "agg-dossier_name": "Dossier name",
};

export function SearchDialogContent({
  dossiers,
  hasSearched,
  setHasSearched,
}: {
  dossiers: DossierItem[];
  hasSearched: boolean;
  setHasSearched: (hasSearched: boolean) => void;
}) {
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTabView, setActiveTabView] = useState("new-search");

  // Voor tabs
  const [advanced, setAdvanced] = useState(false);

  const RESULTS_PER_PAGE = 10;

  const [showDossierSheet, setShowDossierSheet] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResultHit | null>(
    null
  );

  const { filters, setFilter } = useSearchStore();

  const { data, isPending } = useDashboardSearch(
    searchQuery,
    filters,
    hasSearched
  );

  const searchResults = data?.hits ?? [];
  const totalResults = data?.results ?? 0;
  const aggregations = data?.aggregations ?? {};
  const filterDefs = Object.keys(aggregations).map((k) => ({
    key: k,
    label: AGGREGATION_LABELS[k] ?? k,
  }));
  const handleSearch = () => {
    if (searchInput.trim()) {
      setSearchQuery(searchInput);
      setHasSearched(true);
      setCurrentPage(1);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  // Pagination logic
  const totalPages = Math.ceil(searchResults.length / RESULTS_PER_PAGE);
  const paginatedResults = searchResults.slice(
    (currentPage - 1) * RESULTS_PER_PAGE,
    currentPage * RESULTS_PER_PAGE
  );

  // INITIËLE STAAT: Tabs + compacte zoekbalk
  if (!hasSearched) {
    return (
      <div className="transition-all duration-300 ease-in-out h-[450px] overflow-hidden">
        <h1 className="text-2xl font-bold text-center mb-8">Zoeken</h1>
        <div className="px-12 pb-8">
          <Tabs
            defaultValue="new-search"
            value={activeTabView}
            onValueChange={setActiveTabView}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2 bg-white">
              <TabsTrigger
                value="new-search"
                className="data-[state=active]:bg-gray-50 rounded-t-lg"
              >
                Nieuwe zoekopdracht
              </TabsTrigger>
              <TabsTrigger
                value="saved-searches"
                className="data-[state=active]:bg-gray-50 rounded-t-lg"
              >
                Opgeslagen zoekopdrachten
              </TabsTrigger>
            </TabsList>
            <TabsContent value="new-search" className="space-y-6 ">
              {/* Search Input + Bewaar */}
              <div className="mb-8 bg-gray-50 p-4 flex items-center gap-4">
                <div className="relative flex-1 max-w-4xl mx-auto">
                  <span className="absolute left-4 top-1/2 transform -translate-y-1/2">
                    <Search className="text-lintblauw h-5 w-5" />
                  </span>
                  <Input
                    placeholder="Zoek op onderwerp, document, persoon..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyUp={handleKeyPress}
                    className="pl-14 pr-14 py-4 text-base border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:ring-0 bg-white"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 p-2"
                    tabIndex={-1}
                  >
                    <Mic className="h-5 w-5 text-lintblauw" />
                  </Button>
                </div>
              </div>
              {/* Statistics */}
              <div className="text-center text-sm text-gray-700 mb-6">
                Indexeert{" "}
                <span className="font-semibold text-lintblauw">
                  341.498.109
                </span>{" "}
                documenten en{" "}
                <span className="font-semibold text-lintblauw">45.496.209</span>{" "}
                artikelen uit{" "}
                <span className="font-semibold text-lintblauw">378</span>{" "}
                bronnen
              </div>
            </TabsContent>
            <TabsContent
              value="saved-searches"
              className="space-y-4 bg-gray-50"
            >
              <div className="text-center text-gray-500 py-8">
                <p>Geen opgeslagen zoekopdrachten gevonden</p>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    );
  }

  // NA ZOEKEN: Uitgebreid zoekresultaten-scherm
  return (
    <div className="w-full h-full flex flex-col overflow-y-auto bg-gray-50">
      {/* Titel Zoekresultaten + Geavanceerd zoeken switch rechts */}
      <div className="px-10 pt-6 pb-2 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Zoekresultaten</h2>
        <div className="flex items-center gap-2">
          <Switch
            id="advanced-search-modal"
            checked={advanced}
            onCheckedChange={setAdvanced}
            className="data-[state=checked]:bg-lintblauw data-[state=unchecked]:bg-gray-400 cursor-pointer"
          />
          <label
            htmlFor="advanced-search-modal"
            className="text-sm text-gray-700 select-none cursor-pointer"
          >
            Geavanceerd zoeken
          </label>
        </div>
      </div>
      {/* Sticky header: zoekbalk, tabs, filters */}
      <div className="sticky top-0 z-20 bg-gray-50 border-b">
        <div className="px-10 pt-2 pb-4 bg-gray-50">
          <div className="relative w-full flex items-center gap-3">
            {/* Input wrapper met search en mic in input */}
            <div className="relative flex-1">
              <span className="absolute left-4 top-1/2 transform -translate-y-1/2">
                <Search className="text-lintblauw h-5 w-5" />
              </span>
              <Input
                placeholder="Zoekopdracht..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyUp={handleKeyPress}
                className="pl-12 pr-14 py-4 text-base border-2 border-gray-300 rounded-lg focus:border-lintblauw focus:ring-0 bg-white w-full"
              />
              <span className="absolute right-4 top-1/2 transform -translate-y-1/2 cursor-pointer">
                <Mic className="h-5 w-5 text-lintblauw" />
              </span>
            </div>
            {/* Lintblauw 'Bewaar zoekopdracht' button */}
            <Button
              variant="default"
              size="sm"
              className="ml-4 whitespace-nowrap flex-shrink-0 bg-lintblauw text-white hover:bg-lintblauw/90"
            >
              Bewaar zoekopdracht
            </Button>
          </div>
        </div>
        {/* Bron-tabs */}
        {/**
        <div
          className="flex gap-2 pt-2 border-b border-gray-200 bg-gray-50 px-10"
          style={{ marginLeft: 0, marginRight: 0 }}
        >
          {SOURCE_TABS.map((tab) => (
            <Button
              key={tab}
              variant="ghost"
              className={`px-4 py-2 text-sm focus-visible:bg-transparent rounded-t-lg rounded-b-none font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? "border-lintblauw text-lintblauw"
                  : "border-transparent text-gray-600 hover:bg-lintblauw/5 hover:border-lintblauw"
              }`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </Button>
          ))}
        </div>
        */}
        {/* Filters */}
        <div
          className="flex gap-3 py-3 border-b border-gray-200 bg-gray-50"
          style={{
            marginLeft: 0,
            marginRight: 0,
            paddingLeft: 40,
            paddingRight: 40,
          }}
        >
          {filterDefs.map((filter) => (
            <DropdownMenu key={filter.key}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className={`flex items-center gap-2 text-lintblauw px-4 py-2 rounded shadow-none hover:bg-lintblauw/5 focus:bg-lintblauw/10 focus:text-lintblauw active:bg-lintblauw/10 active:text-lintblauw `}
                >
                  {filter.label}
                  <ChevronDown className="w-4 h-4 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {aggregations[filter.key]?.buckets?.map((b: any) => (
                  <DropdownMenuItem
                    key={b.key}
                    className={
                      filters[filter.key] === b.key ? "bg-gray-100" : ""
                    }
                    onSelect={() => {
                      setFilter(filter.key, b.key);
                      setCurrentPage(1);
                    }}
                  >
                    {formatBucketValue(b)}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          ))}
        </div>

        <div className="flex items-center justify-start px-10 pb-2 bg-gray-50 pt-2">
          <div className="text-gray-700 text-sm">{totalResults} resultaten</div>
        </div>
      </div>
      {/* Scrollable results area */}
      <div className="flex-1 overflow-y-auto px-10 py-2 bg-gray-50">
        {isPending ? (
          <div className="text-center py-12 text-gray-500 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-lintblauw" />
          </div>
        ) : (
          <div className="space-y-4">
            {paginatedResults.map((result) => {
              const src = result._source;
              const isActive = selectedResult?._id === result._id;
              return (
                <div
                  key={result._id}
                  onClick={() => setSelectedResult(result)}
                  className={`border rounded-lg p-4 bg-white cursor-pointer flex gap-4 hover:shadow-md transition ${
                    isActive ? "border-2 border-lintblauw" : ""
                  }`}
                >
                  <div className="w-16 h-16 bg-lintblauw/10 rounded flex items-center justify-center flex-shrink-0">
                    <div className="w-8 h-8 bg-lintblauw rounded-sm flex items-center justify-center text-white font-bold text-lg">
                      {src.filetype?.[0] || "D"}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-lintblauw text-lg block truncate">
                      {src.title}
                    </div>
                    <div className="flex flex-wrap gap-2 items-center mt-1 mb-1">
                      <span className="text-xs text-gray-500">
                        {src.filetype}
                      </span>
                      <span className="text-xs text-gray-400">{src.size}</span>
                      <span className="text-xs text-gray-400">
                        {src.author}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(src.datetime_published).toLocaleDateString(
                          "nl-NL"
                        )}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1 line-clamp-2">
                      {src.full_text?.slice(0, 180)}...
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        {/* Paginering */}
        <div className="flex justify-center items-center gap-2 mt-8 mb-4">
          <Button
            variant="outline"
            size="sm"
            className="px-3"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          >
            &lt;
          </Button>
          {Array.from({ length: totalPages }).map((_, idx) => (
            <Button
              key={idx}
              variant={currentPage === idx + 1 ? "default" : "outline"}
              size="sm"
              className={`px-3 ${
                currentPage === idx + 1 ? "bg-lintblauw text-white" : ""
              }`}
              onClick={() => setCurrentPage(idx + 1)}
            >
              {idx + 1}
            </Button>
          ))}
          <Button
            variant="outline"
            size="sm"
            className="px-3"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          >
            &gt;
          </Button>
        </div>
      </div>

      {/* Sheet voor bron details */}
      <Sheet
        open={!!selectedResult}
        onOpenChange={(open) => !open && setSelectedResult(null)}
      >
        <SheetTitle className="sr-only">Bron detail</SheetTitle>
        <SheetContent side="right" className="w-full max-w-xl p-0">
          {selectedResult && (
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between px-6 pt-12 pb-4 border-b">
                <h2 className="text-xl font-bold hyphens-auto break-words min-w-0">
                  {selectedResult._source.title}
                </h2>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowDossierSheet(true)}
                  >
                    <FolderPlus className="w-5 h-5" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <Share2 className="w-5 h-5" />
                  </Button>
                  <Button variant="ghost" size="icon">
                    <Flag className="w-5 h-5" />
                  </Button>
                </div>
              </div>
              <div className="p-6 overflow-y-auto space-y-2 flex-1">
                <div className="text-sm text-gray-500 overflow-hidden whitespace-nowrap text-ellipsis">
                  {selectedResult._source.filepath}
                </div>
                <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                  <span>{selectedResult._source.filetype}</span>
                  <span>{selectedResult._source.size}</span>
                  <span>{selectedResult._source.author}</span>
                  <span>
                    {new Date(
                      selectedResult._source.datetime_published
                    ).toLocaleDateString("nl-NL")}
                  </span>
                </div>
                <div className="mt-6" />

                <p className="text-sm mt-4">
                  {selectedResult._source.full_text?.slice(0, 500)}...
                </p>
                {/* --- Nieuwe velden onderin --- */}
                <div className="flex flex-col gap-2 mt-2 mb-2">
                  {selectedResult._source.werkprocess && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 min-w-[110px]">
                        Werkproces:
                      </span>
                      <Badge
                        variant="outline"
                        className="rounded-full px-2 py-1 text-xs bg-gray-100 text-gray-700"
                      >
                        {selectedResult._source.werkprocess}
                      </Badge>
                    </div>
                  )}
                  {selectedResult._source.retention_period && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 min-w-[110px]">
                        Retentieperiode:
                      </span>
                      <Badge
                        variant="outline"
                        className="rounded-full px-2 py-1 text-xs bg-gray-100 text-gray-700"
                      >
                        {selectedResult._source.retention_period}
                      </Badge>
                    </div>
                  )}
                  {selectedResult._source.weight && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 min-w-[110px]">
                        Gewicht:
                      </span>
                      <Badge
                        variant="outline"
                        className="rounded-full px-2 py-1 text-xs bg-gray-100 text-gray-700"
                      >
                        {selectedResult._source.weight}
                      </Badge>
                    </div>
                  )}
                </div>
                {selectedResult._source.summary && (
                  <div className="text-sm mt-2 text-gray-700">
                    <span className="font-medium text-gray-700 mr-1">
                      Samenvatting:
                    </span>
                    {selectedResult._source.summary}
                  </div>
                )}
                {selectedResult._source.keywords &&
                  selectedResult._source.keywords.length > 0 && (
                    <div className="text-sm mt-2 text-gray-500">
                      <span className="font-medium text-gray-700 mr-1">
                        Keywords:
                      </span>
                      {Array.isArray(selectedResult._source.keywords)
                        ? selectedResult._source.keywords.join(", ")
                        : selectedResult._source.keywords}
                    </div>
                  )}
                {/* --- Einde nieuwe velden onderin --- */}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Sheet voor dossiers */}
      <Sheet open={showDossierSheet} onOpenChange={setShowDossierSheet}>
        <SheetTitle className="sr-only">Voeg toe aan dossier</SheetTitle>
        <SheetContent side="right" className="max-w-md w-full p-0">
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b">
              <h2 className="text-xl font-bold">Voeg toe aan dossier</h2>
            </div>
            <div className="px-6 pt-4 pb-2">
              <button className="w-full flex items-center gap-2 border border-lintblauw text-lintblauw font-medium rounded-md px-4 py-2 mb-4 hover:bg-lintblauw/10 transition bg-white cursor-pointer">
                <span className="text-xl leading-none">+</span>
                Nieuw dossier aanmaken
              </button>
              <div className="flex flex-col gap-3">
                {dossiers.map((dos) => (
                  <div
                    key={dos.name}
                    className="bg-white rounded-md border p-3 flex flex-col gap-1 shadow-sm cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => handleDossierClick(dos)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{dos.name}</span>
                      {dos.is_unopened ? (
                        <Badge className="bg-green-500 hover:bg-green-600 text-white">
                          Nieuw verzoek
                        </Badge>
                      ) : null}
                    </div>
                    <div className="flex gap-4 text-xs text-gray-400 mt-1">
                      <span>
                        Ontvangen{" "}
                        {new Date(dos.date_received).toLocaleString("nl-NL", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

function handleDossierClick(dos: DossierItem) {
  console.log("dossier", dos);
  toast.success("Toegevoegd aan dossier");
}
