import { fetch } from "wix-fetch";
import wixLocation from "wix-location";

const API_BASE_URL = "https://YOUR-APP-NAME.onrender.com";
let history = [];
let lastInteractionId = null;

$w.onReady(() => {
  $w("#boxSavePlan").collapse();
  $w("#boxMembershipInvite").collapse();
  $w("#btnAsk").onClick(handleAsk);
  $w("#btnSavePlan").onClick(handleSavePlan);
  $w("#btnJoin").onClick(() => wixLocation.to("/profil"));
  $w("#btnLater").onClick(() => $w("#boxMembershipInvite").collapse());
});

async function handleAsk() {
  const question = ($w("#inputQuestion").value || "").trim();
  if (!question) return setReply("Lütfen planlamak istediğin etkinliği anlat.");
  $w("#btnAsk").disable();
  setReply("Kişisel planın hazırlanıyor…");
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:question,history})});
    const data = await response.json();
    setReply(data.success ? data.reply : (data.error || "Yanıt alınamadı."));
    if (data.success) {
      history.push({role:"user",content:question},{role:"assistant",content:data.reply});
      lastInteractionId = data.interaction_id;
      $w("#boxSavePlan").expand();
    }
  } finally { $w("#btnAsk").enable(); }
}

async function handleSavePlan() {
  const response = await fetch(`${API_BASE_URL}/api/leads`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    name:$w("#inputName").value,
    phone:$w("#inputPhone").value,
    message:history.at(-2)?.content || "",
    interaction_id:lastInteractionId,
    consent:$w("#checkboxConsent").checked,
    history
  })});
  const data = await response.json();
  $w("#textSaveStatus").text = data.success ? data.message : (data.error || "Plan kaydedilemedi.");
  if (data.success) {
    $w("#boxSavePlan").collapse();
    $w("#boxMembershipInvite").expand();
  }
}

function setReply(message) { $w("#textAiReply").text = message; }
