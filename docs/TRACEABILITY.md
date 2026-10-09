# Gereksinim → uygulama → doğrulama

`tests/test_app.py` önceki 19 testi; `tests/test_revision.py` revizyonun 21 testini içerir. “Tarayıcı” satırları otomatik birim testiyle karıştırılmaz. Test adları bu dosyalarda aranabilir.

| Gereksinim | Uygulama | Kanıt / sınır |
|---|---|---|
| Kalıcı kayıt / giriş; özel profil | `app.py:register,login`; `users` | `test_registration_snapshot_and_privacy`, `test_permissions_and_csrf`; tarayıcı kurgusal kayıt ve rol girişleri. |
| Roller, grup, moderatör, bilirkişi | `admin_required`, `expert`; `users.role` | `test_permissions_and_csrf`; rol/grup yönetim ekranı yok. Moderatör `admin` rolüdür. |
| Konu / alt konu / düzenleme | `new_proposal`; `voting.close_voting`; sürüm tabloları | `test_end_to_end_proposal_vote_close_discussion`, `test_all_pages`, `test_stale_edit_cannot_overwrite`; seed alt konu/düzenleme. |
| Sabit seçmen ve r | `voting.start_voting`; `electorate` | `test_registration_snapshot_and_privacy`, `test_deadline_and_policy_two_admins`. |
| Tek güncel oy / değiştirme | `app.py:vote`; bileşik anahtar | `test_unique_vote_and_update`. |
| r=0,50 katılım; çoğunluk | `policy.tally`, Strategy | `test_votes_and_boundaries`, `test_threshold_below_equal_above`; 49/100,50/100,51/100. |
| Çekimser, eşitlik, sıfır seçmen | `policy.tally` | `test_votes_and_boundaries`; sıfır payda güvenli. |
| Süre sonu ve tek kapanış | `prepare`, `close_voting` | `test_expired_vote_closes_once_and_rejects_late_vote`; tarayıcı ayrı DB'de test saati hızlandırıldı. |
| Kural engeli ve grup katılımı | `RuleHandler`, `check_rules`; `applied` | `test_majority_cannot_override_rule`, `test_group_and_restrictive_rules`, `test_chain_collects_multiple_failures`, `test_two_thirds_exact_boundary`; tarayıcı hazır R1 kararı. |
| Gerekçe, azınlık, itiraz | `proposal,appeal,respond` | `test_appeal_and_response_permissions`; tarayıcı yeni kararda 2 kabul +1 ret gerekçeleri açıldı. |
| Tartışma, geçmiş, güvenli metin | `message,edit_message,history` | `test_message_persistence_history_and_escape`; tarayıcı karşı gerekçe kalıcı. |
| Kaldırma ve geçici gizleme | `hide,restore`; remove/remove_section | `test_emergency_hide_and_review`, `test_section_removal_keeps_later_messages`, `test_permanent_hide_cannot_become_temporary`, `test_spam_and_hidden_edit_permissions`. |
| Sorular / kaynak / akran açıklaması | `messages.kind`; URL denetimi | Kalıcılık testleri; tarayıcı bağlantısız kaynak hatasında metin/tür korundu. |
| Tekrarsız katkı puanı / spam | `storage.award`, `helpful`, `message` | `test_helpfulness_dedup_and_self_rating`, `test_daily_points_cap`, `test_spam_and_hidden_edit_permissions`; çoklu sahte hesap tam çözülmez. |
| Dashboard / takip | `index,contributions,follow,notify` | `test_all_pages`, `test_topic_follow_notification`; tarayıcı yeni hesap boş durumu. |
| İlişki grafı | `graph`; `templates/graph.html` | `test_all_pages`; SQL filtre/LIMIT; görünüm sınırlı şema ve erişilebilir listedir. |
| Bilirkişi | `expert`, opinions, expert_requests | `test_permissions_and_csrf`; seed danışma görüşü. Her uzman akışı tarayıcıdan yeniden yürütülmedi. |
| AI yardımcı | `SummaryService`, `DemoProvider` | `SummaryTests` 9 sentetik durum; `test_old_minority_and_paginated_source_survive`, `test_provider_failure_keeps_voting_working_and_summary_read_only`, `test_unsupported_config_does_not_prevent_login`. Dış model yok. |
| Hash zinciri ve kopya demo | `event_digest,verify_events`, `storage.event`, scripts | `test_hash_chain_tampering`; verify/replicate komutları çalıştırıldı. Gerçek dağıtık defter değil. |
| Müzakere markası / mobil / PWA | templates, static, manifest | Mobil 390×844 özet görsel denetimi; sunucu HTML sayfaları; fiziksel cihaz PWA kurulumu yapılmadı. |
| Diyagram / rapor | `docs/diagrams/render.py`, `docs/build_report.py` | SVG'ler görsel açıldı; PDF A4 tek sayfa ve URI annotasyonu kontrol edildi. |

Kapsamın çalışıyor olması üretim olgunluğu anlamına gelmez. Gerçek AI, kimlik doğrulama sağlayıcısı, ölçek/yük sonuçları, native mobil ve bağımsız dağıtık mutabakat bulunmaz.
