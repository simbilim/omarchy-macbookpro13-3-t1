# Omarchy MacBook: analyse en plan, 21 september 2026

Onderzocht via SSH op de MacBookPro13,3. Bestaande logs van 19 september bevatten voldoende bewijs voor een ernstig slaapverbruikprobleem. De eerdere korte slaaptests van 9 september bewezen herstel van de desktop, maar geen laag stroomverbruik. Het oorspronkelijke plan hieronder is op 21 september in uitvoering genomen; de actuele resultaten staan direct hieronder.

## Oplossing, 15 oktober 2026

**s2idle kan dit doel op deze hardware niet halen.** Ook wakker met scherm uit bleef het CPU-pakket 0% in PC6–PC10 (MSR-tellers), terwijl de limiet in `MSR_PKG_CST_CONFIG_CONTROL` PC10 toestaat en niet vergrendeld is. Tijdelijk runtime-suspenderen van beide Thunderbolt-bomen, de Radeon-root-port en de PCH-xHCI verlaagde het pakketvermogen van 2,8 naar 1,4 W, maar PC6 bleef 0%. De PMC-registers lezen 0xffffffff; Apple-firmware verbergt de PMC. Een MacBookPro14,3-eigenaar meldt hetzelfde vanaf een standaard Arch-live-USB.

**S3 werkt met één aanvulling.** Apple-firmware schakelt in S3 beide Alpine Ridge-controllers uit en herstelt hun PCIe-bomen niet. Linux wacht bij hervatten dan circa 70 s per controller en verliest beide USB-C-xHCI's. De slaaphelper verwijdert nu vóór S3 beide ingebouwde upstreambruggen (`8086:1578` onder PEG1/PEG2) en voert na wake een PCI-rescan uit; de firmware heeft ze dan weer gevoed. Metingen op accu, zonder kabels:

| Test | Resultaat |
| --- | --- |
| 90 s S3, Radeon gevoed | hervat zelfstandig, beide xHCI's terug na rescan |
| 604 s S3, Radeon uit | 1972 → 1970 mAh (circa 0,1–0,2 W; meterresolutie 1 mAh), hervatten 2,4 s |
| `systemctl suspend` met nieuwe helper | trees verwijderd en teruggezet, Radeon weer uit, displays gewekt, geen mislukte units |

De firmware zet de Radeon na S3 weer aan; de bestaande `macbook-t1-radeon-off`-stap in `post` schakelt hem weer uit. Het ACPI-pad dat macOS gebruikt (`NHI0.SXFP(0)` vóór S3, en `RTPC`/`RTBT`/`RUSB` voor runtime-uitschakeling) is onderzocht en met een eigen module getest, maar is niet nodig en niet opgenomen. De ACPI-dumps staan niet in deze repo.

Fysieke klepcycli bevestigden daarna drie aanvullingen. (1) De BCM43602 meldde na een tweede S3-cyclus een hardwareblokkade en weigerde iedere associatie (status 16); de helper herlaadt `brcmfmac` nu rond S3. (2) De T1 hield de Touch Bar na S3 donker, ook na driver-herladen, USB-reset en de `t1-touchbar`-activatie; `ASOC.SOCW(1)` (EC-mailbox "host wakker", zoals macOS) herstelt hem. De eigen DKMS-module `macbook-t1-socw` roept dit na iedere resume aan. (3) Met de USB-ethernet aangesloten tijdens S3 kwam die linker controller niet terug; ook `PEG1._PS3`/`_PS0` en `UPSB._PS0` brachten de link niet op, pas een herstart wel. De helper kiest daarom s2idle zolang een USB-apparaat op een USB-C-poort hangt; getest met ethernet aangesloten: s2idle, beide controllers behouden.

Hervattijd: in S3 komt het scherm na circa 2–3 s terug. De kernel-resume duurde in de laatste klepcyclus 6,8 s, waarvan 4,7 s in `i915` `pci_pm_resume` zonder logregels en 1,0 s in de NVMe-root-port 00:1b.0. In de s2idle-terugval (USB-C-apparaat aangesloten) kost de Thunderbolt-AML in `pci_pm_resume_noirq` circa 17 s, wat het langdurig donkere scherm bij openen verklaart.

De s2idle-vertraging is opgelost met de eigen DKMS-module `macbook-t1-tb-nod3`. Die zet `PCI_DEV_FLAGS_NO_D3` op de twee ingebouwde Alpine Ridge-upstreambruggen (`8086:1578`) en beide USB-C-xHCI's (`8086:15d4`) onder PEG1/PEG2, ook na de PCI-rescan via een busnotifier. Zonder D3 draaien hun trage `_PS3`/`_PS0` niet meer. Meting met ethernet en lader aangesloten: hervatten van 20,7 s (04:00.0 8,7 s, 7a:00.0 8,3 s, xHCI's 2 × 1,0 s) naar 1,0 s; ethernet, wifi en beide controllers bleven werken. `pcie_port_pm=off` is daardoor niet nodig. De helper zet het scherm nu aan vóór de rescan, wifi- en Thunderbolt-herlaadstappen, en herlaadt `brcmfmac` ook rond s2idle: na twee s2idle-cycli zonder herladen weigerde het accesspoint iedere associatie (status 16).

Nachtmeting 15→16 oktober: 16,4 uur S3, 5873 → 5862 mAh (89% → 89%). S3 met alleen de lader aangesloten werkt: beide controllers terug, accu laadt.

De `i915`-resume van 4,7 s na S3 bestond uit circa 350 eDP-AUX-time-outs: de gmux-DDC/AUX-schakelaar wees na S3 nog naar de Radeon, omdat apple-gmux pas na i915 hervatte. De DKMS-module `macbook-t1-gmux-order` legt een device link aan met gmux als supplier van i915. Daarna: 0 AUX-time-outs, `i915` 0,50 s, kernelresume na S3 van 6,8 naar 2,75 s. Resterend: 1,0 s in `pci_pm_resume_noirq` van NVMe-root-port 00:1b.0.

Aanvulling 19 oktober (klep dicht, `Timekeeping suspended for`): met de remove/rescan-stap keerde de eerste S3 op de lader na 3,98 en 3,03 s terug en verdwenen beide USB-C-controllers; de direct volgende S3 hield 582 en 5593 s. Zonder remove/rescan (met `macbook-t1-tb-nod3` actief) hield S3 bij de eerste poging: lader 410,7 en 47,9 s, accu 360,4 en 87,7 s, steeds met beide controllers terug en een werkende USB-ethernet na insteken. De helper verwijdert de bomen daarom niet meer, kent geen laderregel meer en houdt de USB-C-xHCI's na iedere wake in D0. Logind `HoldoffTimeoutSec=5s` en opnieuw slapen bij een gesloten klep na wake vangen vroege wakes af.

Nachtmeting met de vereenvoudigde helper (19→20 oktober): 28,7 uur S3 op accu, 6996 → 6977 mAh (19 mAh), beide USB-C-controllers daarna aanwezig. Een klepcyclus van 3,1 s (klep direct weer open) liet beide Alpine Ridge-bomen zonder voeding; een PCI-rescan vond alleen de upstreambruggen terug. Herstel door een volgende lange S3 is nog niet getest.

Open: herstel van USB-C na een te korte S3; `SOCW(0)` vóór slaap.

## Actuele analyse, 2 oktober 2026

Een afzonderlijke actieve-werksessie op 2 oktober verklaart een deel van het hoge verbruik buiten slaap. UPower registreerde van 13:57:15 tot 15:43:53 een daling van 99,925% naar 35,571% in 106,6 minuten: 36,2 procentpunten per uur. De 212 vermogenssamples hadden een mediaan van 30,47 W en een tijdgewogen gemiddelde van 29,17 W. Tijdens diagnose gebruikte `xdg-desktop-portal-hyprland` onafgebroken vrijwel 100% van één CPU-kern; het CPU-pakket verbruikte circa 13,56 W. De gebruiker bevestigde dat schermdelen eerder was vastgelopen. Dit komt overeen met [upstream issue 433](https://github.com/hyprwm/xdg-desktop-portal-hyprland/issues/433) voor exact `xdg-desktop-portal-hyprland` 1.4.1 en Hyprland 0.56.2: een mislukte screencast na een PipeWire-herstart kan de hoofdthread eindeloos laten draaien.

Omdat geen schermdeling meer actief was, zijn alleen `xdg-desktop-portal-hyprland.service` en `xdg-desktop-portal.service` in de gebruikerssessie herstart. De desktop en applicaties bleven open. In een daaropvolgende meting van 30 seconden verdween de volle-kernbelasting en daalde het CPU-pakket van circa 13,56 naar 2,99 W. De CPU-temperatuur daalde van 73 naar 54 °C; beide ventilatoren draaiden daarna op hun minimum. Dit verklaart de snelle drain tijdens deze werksessie, maar niet de eerder bewezen drain tijdens gesloten slaap.

Upstream heeft op 2 oktober nog geen release met een oplossing: de nieuwste release en het actuele Arch-pakket zijn beide 1.4.1, en issue 433 staat open. Op deze laptop is daarom de concrete trigger duurzaam afgevangen. De systemd-user-drop-in `90-macbook-pipewire-lifecycle.conf` koppelt het Hyprland-portaal met `PartOf=` en `After=` aan `pipewire.service`. Wanneer PipeWire na slaap opnieuw start, krijgt het portaal daardoor ook een nieuwe verbinding voordat een volgende schermdeelaanvraag begint. Een echte PipeWire-herstart veranderde beide proces-ID's, waarna alle audio-/portalservices actief waren en het portaal via D-Bus reageerde. Deze koppeling onderbreekt alleen schermdelen wanneer PipeWire zelf al wordt herstart. Zij is geen algemene upstreamcodefix voor iedere mogelijke screencastfout.

De eerder aangebrachte libinput-quirk bleek nog aanwezig en actief: het touchpad wordt intern herkend en `disable_while_typing=true`. De gevoeligheid stond en staat op de normale waarde nul. Het resterende risico was Hyprlands standaard `tap_and_drag=true`, waardoor een handpalm na een onbedoelde tap een venster kan vastpakken. Het beheerde MacBook-blok in `~/.config/hypr/input.lua` zet nu expliciet `disable_while_typing=true` en `tap_and_drag=false`. Na live herladen meldt Hyprland beide waarden als expliciet ingesteld. Gewoon aanwijzen, tikken, fysiek klikken en scrollen blijven behouden. De onderhoudshelper herstelt dit blok na Omarchy-updates. Snapshot 54 en een privéback-up van de vorige inputconfiguratie zijn vóór de wijziging gemaakt.

Omarchy draait nog op `4.0.4-1` met `6.18.49-3-lts`. De nacht van 1 op 2 oktober bevat één s2idle-cyclus: start 21:53:21, terugkeer 09:06:24, eindmeting 09:06:26. Over 40.384 seconden daalde de accu van 67% naar 5%, en de lading van 4.471 naar 331 mAh. Dit is 62 procentpunten verlies in ongeveer 11 uur en 13 minuten. De beginmeting was zonder voeding; bij de eindmeting was de lader aangesloten. Daarom is geen zuivere gemiddelde vermogensmeting beschikbaar. De accu was bij terugkeer niet volledig leeg. De gemeten accutemperatuur daalde van 36,5 naar 29,5 °C; deze eindpunten bewijzen geen warmteontwikkeling tijdens deze nacht.

De bootidentiteit van de pre- en postmeting komt overeen met de huidige boot, en Hyprland draait sinds 1 oktober 20:39:51. Vanochtend is dus dezelfde desktop hervat. Er zijn geen tussentijdse volledige hervattingen vastgelegd. Vóór slaap waren de audio-PCM-streams gesloten, alle drie xHCI-wakepaden en Apple SPI-wake uitgeschakeld en GPE17 gemaskeerd. GPE17 steeg tijdens de cyclus slechts met één. De aanpassingen tegen deze wakebronnen en open audiostreams zijn daarmee onvoldoende om het accuprobleem op te lossen. De package-C6–C10-tellers namen niet toe; de ongeldige SLP_S0-teller blijft buiten de conclusie. De precieze stroomverbruiker is nog niet aangetoond.

De twee Thunderbolt-upstreambruggen kostten bij `pci_pm_resume_noirq` opnieuw 6,227 en 6,217 seconden, samen 12,444 seconden. Dit bevestigt de hervattingsvertraging, maar verklaart niet het nachtelijke accuverlies.

De extra firmwaremeting van 30 september is niet beschikbaar. Die slaappoging begon om 16:55:35; de laatste bewaarde serviceregel meldt het bevriezen van `user.slice`. Een postmeting en voltooid tracebestand ontbreken. Om 21:18 volgt een nieuwe boot. De log bewijst niet waarom de eerdere sessie eindigde, of welke rol de tijdelijke meetcode daarbij had. De vluchtige meetconfiguratie is inmiddels verdwenen en is niet opnieuw geactiveerd.

De Touch Bar-driver registreerde vanochtend zowel suspend als resume, zonder bijbehorende foutmelding. Om 09:06:34 herstelde de schermvolgservice haar actieve instelling; om 09:12:03 schakelde zij de balk weer uit omdat het laptopscherm uit stond. Bij inspectie waren zowel DRM als Hyprland inderdaad op scherm-uit ingesteld en stond de Touch Bar op `idle_timeout=-2`. Een gerichte DPMS-enable via de actieve Hyprland-Lua-interface zette om 09:29:32 het scherm aan en de Touch Bar automatisch terug naar `idle_timeout=-1`. Dit bewijst herstel van de software-instelling, niet dat de fysieke balk weer beeld geeft. Visuele bevestiging door de gebruiker staat nog open. Er zijn geen drivers herladen, slaapinstellingen veranderd of nieuwe slaaptests gestart.

De gebruiker verduidelijkte vervolgens dat de Touch Bar wel beeld gaf, maar aanrakingen niets deden. De schermvolgservice verklaart dat symptoom dus niet. Een meting uitsluitend op de Touch Bar-inputnode registreerde 84 toetsgebeurtenissen tijdens de bediening, terwijl het volume volgens de gebruiker niet veranderde. Driverdebug toonde `want_mode=2` (mediaknoppen), `cur-mode=3` (uit), met het display wel aan. De T1-modusfunctie retourneerde de positieve bytecount van `usb_control_msg`, terwijl de worker uitsluitend bij nul de actuele modus bijwerkt. Na suspend bleef de software daardoor op uit staan; de eventhandler onderdrukt in die toestand de normale toetsen en genereert dummy-events.

De gerichte drivercorrectie normaliseert uitsluitend de T1-overdracht van precies één byte naar succeswaarde nul; negatieve USB-fouten blijven intact en een onvolledige overdracht wordt `-EIO`. De bestaande onderhoudshelper past dit samen met de resume-correctie toe en weigert onbekende broncodepatronen. Vier migratie-/idempotentietests slagen. Snapshot 53 en broncode-, helper- en modulebackups zijn vóór installatie gemaakt. Beide kernelmodules en UKI’s zijn herbouwd; de Limine-hashes zijn gecontroleerd. Alleen de Touch Bar-module is herladen, met behoud van boot en desktop. Een gerichte uit/aan-proef toont nu de correcte overgang van interne modus 3 (uit) naar 2 (mediaknoppen). De geladen module komt overeen met de geïnstalleerde correctie. De gebruiker bevestigde daarna dat de Touch Bar-knoppen weer werken. Een latere slaap/hervatcyclus met de gecorrigeerde driver moet nog worden gecontroleerd. Deze Touch Bar-fout is geen bewezen verklaring voor de batterijdrain.

De ruwe geselecteerde service- en kernellogs zijn privé bewaard op de laptop in `/var/lib/macbook-t1-omarchy/sleep-investigation-20261002`, met beperkte toegangsrechten. De nachtelijke batterijdrain blijft onopgelost.

## Uitvoeringsstatus, 22 september 2026

- De historische diagnose- en updatesnapshots zijn na de geslaagde duurtest opgeruimd. Er blijven twee herstelpunten: snapshot 44 als rollback van vóór slaap/trackpadwerk en snapshot 45 van de bewezen stabiele Intel-s2idle-configuratie. Limine toont per snapshot alleen LTS.
- Omarchy is bijgewerkt van 4.0.2 naar 4.0.4. De actieve en standaard geladen kernel is `6.18.49-3-lts`. Alleen LTS en `linux-omarchy` `7.2.5-3` met hun headers zijn behouden; het overbodige gewone `linux`-pakket is verwijderd en circa 466 MB is vrijgekomen. Apple-input en CS8409-audio zijn via DKMS voor beide behouden kernels gebouwd.
- Limine start automatisch `Omarchy LTS - MacBook`. Safe Graphics en Console gebruiken de `linux-omarchy`-image als uitwijkroute; de beheerhelper verifieert en vernieuwt voortaan de BLAKE2-hashes van alle drie beheerde ingangen.
- De lokale libinput-quirk classificeert `Apple SPI Keyboard` op dit model als intern. Een nieuwe compositorcontext meldt `disable_while_typing=true`, met normale gevoeligheid 0 en zonder wijzigingen aan scrollen, tikken of palmgrenzen.
- De slaaphelper schakelt de drie xHCI-wakebronnen alleen bij een gesloten klep tijdelijk uit en herstelt hun exacte vorige toestand. De meettool registreert per cyclus lading, spanning, wake-IRQ en gewijzigde ACPI-GPE-tellers.
- De normale desktop gebruikt alleen Intel; amdgpu is geblokkeerd en de ongebruikte Radeon wordt na de desktopstart veilig via Apple GMUX uitgezet. De daadwerkelijke Radeon-voeding tijdens het volledige slaapinterval is daarmee nog niet gemeten.
- Deep/S3 is afgewezen: Apple-firmware schakelt daarbij beide Alpine Ridge PCIe-bomen uit, waarna de twee USB-C-xHCI-controllers niet terugkomen. Cold hibernation restore reset vóór userspace op zowel LTS als `linux-omarchy`; een gemarkeerde swapheader bewees dat de herstelpoging wel begon. De tijdelijke hibernatiehook en diagnosemodule zijn verwijderd.
- De eerste s2idle-proef na reboot onthulde een volgordefout: systemd koos s2idle pas na de pre-hook, waardoor die hook de Thunderbolt NHI niet verwijderde. De helper kiest s2idle nu ook zelf vóór de apparaatvoorbereiding.
- De gecontroleerde herhaling sliep 103 seconden en hervatte binnen dezelfde boot en Hyprland-sessie. Beide externe xHCI-controllers kwamen zonder fout terug, USB-netwerk bleef werken, Touch Bar/audio waren actief, Radeon bleef uit en er waren geen mislukte units. Deze proef liep aan de lader en meet daarom geen slaapverbruik.
- De fysieke proef van 5.409 seconden (90 minuten en 9 seconden) hervatte dezelfde boot en Hyprland-sessie met aanwezige USB-C-controllers en actieve Touch Bar-services. De lading daalde netto 61 mAh. Het oorspronkelijke cijfer van circa 0,515 W geldt niet meer als schone accu-referentie: herlezing op 30 september toont `Discharging` vóór slaap maar `Charging` bij de eindmeting. Het moment en de bijdrage van de voedingsaansluiting zijn daarmee onvoldoende bepaald.
- Die lage nulmeting bleek niet representatief voor een normale werksessie. Een applicatie-actieve tascyclus verbruikte later 8,660 W; een volgende nachtproef liep ondanks bewezen uitschakeling van Apple SPI en alle xHCI-wakebronnen vanaf 55% volledig leeg. De CS8409-driver bleek een lege Mac-specifieke suspendcallback te hebben terwijl actieve PCM-cleanup de speakerversterkers wel uitschakelt. De slaaptransactie sluit daarom nu eerst de gebruikersaudio en herstelt die na wake. Het sluiten en herstellen van audio is live getest; de later teruggevonden duurtest van 25 september laat zien dat deze ingreep het accuprobleem niet oploste.
- Een afsluitende herstart koos zonder handmatige selectie `6.18.49-3-lts`. De desktop, Intel-driver, Touch Bar-services en beide DKMS-stacks startten; er waren geen mislukte systemd-units. Het Limine-menu bevat alleen de stabiele LTS-keuze, twee actuele rescue-opties, de twee LTS-snapshots en EFI fallback.
- De duurtest op 25 september hervatte na 7.298 seconden dezelfde boot en Hyprland-sessie, maar verbruikte naar schatting 2,514 W. De toen gemelde nul SLP_S0-residentie is ingetrokken: de teller gaf een onbetrouwbare all-ones-registerwaarde terug. De USB-netwerkadapter bleek tijdens de hele slaap nog aan de linker Thunderbolt-xHCI te hangen, zodat dit geen losgekoppelde nulmeting was. Tegelijk bleven de package-C6 tot en met C10-tellers sinds boot op nul, terwijl losse cores wel C10 gebruikten. Apple zet in de FADT zowel Low Power S0 Idle als PCIe-ASPM-ondersteuning uit; de twee Thunderbolt-rootlinks staan inderdaad zonder ASPM. De meethelper registreert package-C-state-delta's en slaat de S0ix-conclusie over bij de ongeldige teller. ASPM blijft een hypothese, geen bewezen oorzaak.


## Aanvulling, 30 september 2026

De daaropvolgende gecontroleerde NHI-D3hot-proef leverde geen reproduceerbare besparing op. De vier korte accumetingen in volgorde standaard/aangepast/aangepast/standaard waren 11,34 / 5,80 / 10,97 / 5,45 W inclusief hervatten; gewogen over beide metingen per instelling komen beide op circa 8,4 W. Alle sessies en USB-C-controllers herstelden, maar de tijdelijke wijziging is verwijderd. Kerneltracing lokaliseert de circa 12,4 seconden hervattingsvertraging in de ACPI-powertransities van de twee Thunderbolt-upstreambruggen. Zie de meettabel en beperkingen in [mobile-profile.md](mobile-profile.md). De nachtelijke drain is niet opgelost.

De later uitgelezen logs bevatten al een losgekoppelde duurtest op 25 september: USB-netwerk los om 15:25:26, één s2idle-cyclus van 15:29 tot 20:17. De accu daalde van 93% naar 26% (4.419 mAh in 17.303 seconden; geschat 10,281 W) en de accutemperatuur steeg van 33,5 naar 41,5 °C. Audiostreams waren gesloten, USB-/SPI-wake uitgeschakeld en GPE17 gemaskeerd. De slaapstroom is dus nog steeds onacceptabel. Voor bewijs van die tekortkoming hoeft de gebruiker geen volgende duurtest te doen.

De SLP_S0-teller bleek exact 0xffffffff × 104 te bevatten. De eerdere uitspraak dat nul S0ix bewezen was, vervalt. De package-C-state-tellers gebruiken afzonderlijke MSR-metingen en blijven relevant; zij tonen in deze cyclus alleen groei in C2/C3. De firmwareflags en ASPM-instellingen bewijzen niet welke component het hoge verbruik veroorzaakt. Zie [de bijgewerkte meetanalyse](mobile-profile.md#evidence-correction-and-recovered-duration-test-30-september-2026).

## 1. Installatie en opstartmenu

| Onderdeel | Aangetroffen toestand | Beoordeling |
| --- | --- | --- |
| Omarchy | 4.0.2-1; instellingenpakket eveneens 4.0.2-1 | Eén actieve Omarchy-installatie |
| Actieve Linux-kernel | 6.18.46-1-lts | De bedoelde LTS-kernel wordt geladen |
| Tweede kernel | 7.1.9-arch1-2 | Bestaande alternatieve kernel; eerdere grafische/hibernateproblemen maken dit geen bewezen stabiele uitwijkoptie |
| DKMS | Touch Bar- en CS8409-modules voor beide kernels geïnstalleerd | Headers blijven nodig voor toekomstige modulebouw |
| Limine | Eerste/default-keuze: Omarchy LTS - MacBook; timeout 1 seconde | Controleprogramma bevestigt dat LTS-menuverwijzing en image-hash kloppen |
| Overige menuopties | Safe Graphics, Console, gegenereerde linux/linux-lts en 21 snapshots | Veel opties, maar geen 21 afzonderlijke actuele OS-installaties |
| Apple-partitie | APFS-partitie van circa 74,5 GiB aanwezig | Waarschijnlijk de behouden macOS-installatie; versie en opstartbaarheid niet onderzocht |
| Vrije ruimte | Root circa 128 GiB, boot circa 1,5 GiB vrij | Geen acute noodzaak kernels of snapshots te wissen |

Safe Graphics en Console verwijzen allebei naar dezelfde niet-LTS-kernelimage. Ze zijn verschillende opstartprofielen. Een snapshot herstelt een eerdere systeemtoestand; dit is iets anders dan een extra kernelpakket.

Advies: LTS als standaard behouden. Tijdens slaaponderzoek beide kernelpakketten behouden. Daarna het gewone menu beperken tot de standaardstart en een ingeklapt herstelmenu, met console, één zinvolle alternatieve kernel en enkele geselecteerde snapshots. De oude 7.1.9-kernel pas verwijderen als de vervangende herstelroute getest is. Geen macOS-partitie verwijderen. Snapshotselectie en daadwerkelijke verwijdering zijn afzonderlijke stappen; een eenvoudiger menu vereist geen onmiddellijke vernietiging van herstelpunten.

Let op: snapshot 34 bevat volgens zijn omschrijving het afgewezen vierkanaals-audioprototype. Die is geen voorkeursherstelpunt. Snapshot 32 beschrijft het eerder acceptabele stereoprofiel. Voor nieuw werk een checkpoint van de actuele toestand maken, plus afzonderlijke kopieën van bootbestanden en gewijzigde gebruikersconfiguratie: root-snapshots dekken die niet allemaal.

## 2. Slaapstand: vastgesteld gedrag

De effectieve systemd-instellingen kiezen suspend bij dichtklappen, zowel op accu als aan de lader, met s2idle. Hibernation is uitgeschakeld wegens de eerder gereproduceerde Radeon-resumefout. Docked dichtklappen wordt genegeerd. De oude configuratiebestanden met tegengestelde instellingen bestaan nog, maar latere drop-ins overschrijven ze.

De kernel toont vóór de eerste slaap sinds deze boot `s2idle [deep]`. Dit bewijst hier geen verkeerde slaapkeuze: systemd selecteert s2idle bij suspend; de historische kernelregels bevestigen `PM: suspend entry (s2idle)`.

Op 19 september ging de klep om 17:52 dicht en om 20:45 weer open. Daartussen zijn vijf resumes met nog gesloten klep vastgelegd. Na de eerste korte/afwijkende intervallen volgen wakes ongeveer iedere 40 minuten. Na ongeveer 16–18 seconden gaat het systeem opnieuw slapen. De kernel noemt IRQ 9 en een ACPI non-EC GPE; de exacte veroorzakende GPE/het apparaat is nog niet vastgelegd. RTC-wakealarm was leeg. Er zijn momenteel geen systemd-timers met WakeSystem=yes. Deze feiten wijzen naar verder ACPI/wake-onderzoek, maar bewijzen geen specifieke USB-, Wi-Fi- of batterijoorzaak.

De bestaande pre/post-diagnostiek geeft bovendien hoog verbruik tijdens de slaapintervallen:

| Interval, 19 september | Duur | Verlies lading | Geschat gemiddeld vermogen |
| --- | ---: | ---: | ---: |
| 17:52:46–18:09:36 | 16,8 min | 69 mAh | 3,1 W |
| 18:09:52–18:49:35 | 39,7 min | 546 mAh | 10,2 W |
| 18:49:51–19:29:34 | 39,7 min | 670 mAh | 12,2 W |
| 19:29:52–20:09:36 | 39,7 min | 690 mAh | 12,2 W |
| 20:09:53–20:45:47 | 35,9 min | 645 mAh | 12,3 W |

Berekening: verschil in charge_now × gemiddelde van begin-/eindspanning ÷ verstreken uren. Dit is een schatting uit batterijtelemetrie, inclusief overgangstijd, geen externe vermogensmeting. De procentmeter meldde aanvankelijk 102%; ruwe lading is daarom bruikbaarder dan alleen afgeronde percentages. Van 18:09 tot 20:45 daalde de gerapporteerde capaciteit van 100% naar 62%.

De korte wakes alleen verklaren deze verliezen waarschijnlijk niet. Het systeem bereikt de slaapcode en herstelt de sessie, maar bereikt kennelijk onvoldoende energiebesparing of verlaat intern te vaak de lage vermogensstand. Er zijn in de onderzochte vorige boot geen gematchte Radeon-ringtimeouts/SMU-resumefouten gevonden.

Relevante bestaande mitigaties: Radeon runtime-PM uit, D3cold geblokkeerd en `profile_standard`; tevens conservatieve PCIe/AMDGPU-opstartopties. Die waren bedoeld om de eerdere beeldcrashes te voorkomen. Hun bijdrage aan dit slaapverbruik is nog onbewezen. Het huidige wakkere GPU-vermogen van circa 8 W is geen slaapmeting. Ook `pcie_aspm=off` bewijst niet dat elke link fysiek zonder ASPM werkt: de huidige PCI-registerweergave meldt op GPU/NVMe-links nog L1 enabled.

De slaaphelper schakelt callbacks tijdelijk naar synchroon en verwijdert de ongebruikte Thunderbolt NHI-module; hij herstelt beide na wake en weigert bij aangesloten externe Thunderbolt-apparaten. Dit komt deels overeen met de upstream gemelde aanpak.

## 3. Relevantie van de GitHub-voortgang

De [specifieke reactie van 20 september](https://github.com/omacom/omarchy/pull/10141#issuecomment-5751548433) begrenst de eerste Radeon-watchdogactie en voorkomt automatisch opnieuw proberen na falen. Dit is foutafhandeling; het repareert de onderliggende GPU-reset of slaapstand niet. De PR is nog open/draft. Op deze laptop staat een andere Radeon-oneshot met `profile_standard`, geen exemplaar van die continue MCLK-watchdog. De wijziging is dus niet direct een ontbrekende patch voor deze installatie.

De [update van 15 september](https://github.com/omacom/omarchy/pull/10141#issuecomment-5688899475) noemt een custom 7.2.4-kernel, maar geen nieuwe suspendtest daarop. Dat is geen bewijs dat een overstap vanaf onze LTS-kernel het probleem oplost.

De modelgebonden reactie in [discussie 4695](https://github.com/omacom/omarchy/discussions/4695) is relevanter voor de vervolgdiagnose: dezelfde 13,3 kreeg onbedoelde USB-wakes, waarna tijdelijk uitschakelen van xHCI-wake hielp. Er was ook een EC-wake-module in de gecombineerde oplossing. De afzonderlijke noodzaak daarvan is niet vastgesteld. De testmachine gebruikte een custom kernel en externe USB-root; onze machine gebruikt interne NVMe. Hun langste genoemde kleptest was 15 minuten en accuverbruik is niet gemeten. Daarom geen volledige overname of claim van bewezen zuinige slaap.

## 4. Trackpad

Live Hyprland meldt `disable_while_typing=true`, `tap-to-click=true`, `tap_and_drag=true`, `drag_lock=0`, `drag_3fg=0`, sensitivity=0 en follow_mouse=1. Persoonlijke input.lua bevat alleen uitgecommentarieerde voorbeelden. Automatische focus kan ongewenste pointerbeweging merkbaar versterken; daadwerkelijke vensterverplaatsing moet daarvan onderscheiden worden.

Er is een concrete mismatch in de apparaatregels:

- Ingebouwd toetsenbord heet Apple SPI Keyboard, SPI-bus, vendor 0000.
- Trackpad heet Apple SPI Touchpad, SPI-bus, vendor 06cb/product 06d7.
- De geïnstalleerde Apple SPI-regels vereisen vendor 05ac. Ze matchen beide apparaten dus niet.
- Er zijn geen lokale libinput-overrides. Udev kent de trackpad wel als intern en geeft 160 × 99 mm door.

Dit is een sterke verklaring voor gebrekkige toetsenbordkoppeling/palmherkenning, maar nog geen bewezen volledige oorzaak. Een tijdelijke libinput-context bevestigde dat de trackpad DWT ondersteunt en standaard aan heeft. Er zijn geen toetsaanslagen opgenomen en geen input-events geïnjecteerd. DWT-beschikbaarheid bewijst niet dat de interne toetsenbordkoppeling werkt.

Volgens [libinput](https://wayland.freedesktop.org/libinput/doc/latest/palm-detection.html) is DWT afhankelijk van die koppeling; fysieke klikken en sommige modificatietoetsen blijven uitzonderingen. De [quirk-documentatie](https://wayland.freedesktop.org/libinput/doc/latest/device-quirks.html) beschrijft het matchen en valideren van lokale apparaatregels. Eerst de herkenning corrigeren; snelheid verlagen lost gemiste palmherkenning op zichzelf niet op.

## 5. Uitvoeringsplan en acceptatie

1. **Herstelpunt en opstartbasis vastleggen.** Actuele snapshot, aparte boot-/gebruikersconfigback-ups en LTS/hash/DKMS-controle. LTS behouden; menuweergave vereenvoudigen zodra de herstelroutes bekend zijn. Pakketverwijdering uitstellen tot de slaaptests afgerond zijn. Conflicterende oude slaapbestanden later opschonen tot één duidelijke effectieve policy.
2. **Slaapdiagnostiek verfijnen.** Bestaande batterijmeting aanvullen met ACPI/GPE-trace, wakebronnen, apparaat-suspendcallbacks en beschikbare CPU/package-residencytellers. Vaststellen welk apparaat IRQ 9 veroorzaakt en welke componenten lage vermogensstanden verhinderen. Trace beperkt houden en na de proef stoppen.
3. **Gecontroleerde nulmeting op accu.** Eerst circa één minuut voor betrouwbaar herstel, daarna circa één uur zonder lader/externe apparaten. Die duur overschrijdt het waargenomen 40-minutenpatroon. Lading/spanning/temperatuur vooraf en direct na wake registreren. De gebruiker bedient de klep; openen moet de bestaande sessie herstellen. Vergelijk later afzonderlijk met USB-apparatuur en externe voeding.
4. **Wakes gericht aanpakken.** Alleen bij passende tracegegevens xHCI- of andere apparaat-wake tijdelijk beperken, met herstel van de exacte oude toestand. Klep/ingebouwd toetsenbord als wakepad behouden. Niet de hele ACPI-interrupt of onbekende GPE blind uitschakelen. EC-module pas onderzoeken als klep-wake aantoonbaar ontbreekt; dat is nu niet het hoofdsymptoom.
5. **Verbruik tijdens slaap verlagen.** Eerst op dezelfde LTS-kernel telkens één driver-/powerhypothese testen, op basis van callback/residencygegevens. Radeon-stabiliteitsinstellingen, PCIe, NVMe en Thunderbolt afzonderlijk beoordelen. Na elke wijziging zowel energiemeting als scherm/Touch Bar/audio/Wi-Fi-resume controleren. Een watchdogalternatief is een afzonderlijk experiment, geen bewezen energiebesparing. Bij onvoldoende resultaat gericht een andere kernel/patch of S3-route onderzoeken; deep en hibernation pas heropenen met een concrete oplossing voor de bekende resumefout en een herstelroute.
6. **Trackpad gericht corrigeren.** Een MacBookPro13,3-specifieke lokale quirk laten matchen op naam/bus/model en het ingebouwde toetsenbord expliciet intern classificeren. Parser/matching controleren, inputcontext via passende sessieherstart vernieuwen en fysiek typen met rustende handpalmen testen. Daarna pas zo nodig Apple-trackpadmodel/meetbare palmgrenzen corrigeren. Bij blijvende ongewenste acties tap-and-drag apart uitschakelen; automatische focus aanpassen als dat het ervaren wegduwen blijkt. Normale éénvingerbediening, tweevingerscrollen en klikken behouden en natesten.
7. **Duurtest en afronding.** Minstens tien klepcycli, daarna een proef van één uur en een nacht op accu. Voorstel als streefwaarde: maximaal circa 1% accuverlies per uur, liefst minder; geen merkbare warmteopbouw, ongewenste wakes of verloren sessie. Dit is een acceptatiedoel, geen garantie dat deze hardware/configuratie het haalt. Daarna pas overtollige kernels/herstelpunten opruimen, wijzigingen in de beheerde kit opnemen en updatebestendigheid controleren.

Praktische prioriteit: slaapdiagnose en stroomverbruik eerst; de kleine trackpadherkenningsfix kan zonder kernelwijziging apart worden uitgevoerd. Een geslaagde korte wake-test is voortaan onvoldoende om slaapstand als opgelost aan te merken.
