import { fetch } from "wix-fetch";

const API_BASE_URL = "https://YOUR-APP-NAME.onrender.com";
let allLeads = [];

$w.onReady(async () => {
  $w("#btnRefresh").onClick(loadLeads);
  $w("#inputSearch").onInput(event => filterLeads(event.target.value));
  $w("#repeaterLeads").onItemReady(($item, lead) => {
    $item("#textLeadName").text = lead.isim;
    $item("#textLeadPhone").text = lead.telefon;
    $item("#textUserRequest").text = lead.kullanici_mesaji || lead.mesaj || "—";
    $item("#textAiPlan").text = lead.asistan_yaniti || "—";
    $item("#textLeadStatus").text = "Plan kaydedildi";
    $item("#textLeadDate").text = lead.olusturulma_tarihi || "—";
  });
  await loadLeads();
});

async function loadLeads() {
  $w("#textLoadingStatus").text = "Potansiyel müşteriler yükleniyor…";
  try {
    const response = await fetch(`${API_BASE_URL}/api/leads`);
    const data = await response.json();
    if (!data.success) throw new Error(data.error || "Veri alınamadı.");
    allLeads = data.leads;
    renderLeads(allLeads);
    $w("#textTotalCount").text = String(data.count);
    $w("#textLoadingStatus").text = "";
  } catch (_) { $w("#textLoadingStatus").text = "Kayıtlar yüklenemedi."; }
}

function filterLeads(value) {
  const term = (value || "").toLocaleLowerCase("tr-TR");
  renderLeads(allLeads.filter(lead =>
    lead.isim.toLocaleLowerCase("tr-TR").includes(term) ||
    lead.telefon.includes(term) ||
    (lead.kullanici_mesaji || "").toLocaleLowerCase("tr-TR").includes(term)
  ));
}

function renderLeads(leads) {
  $w("#repeaterLeads").data = leads.map(lead => ({...lead,_id:String(lead.id)}));
}
