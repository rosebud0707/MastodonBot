# MastodonBot
Mastodon(分散型ソーシャルネットワーク)にて動作する、自動返信botアプリケーション  
リプライを検知した場合に外部ファイル(データソース)に記載された文言をランダムに返信する。  
Config.iniにアクセストークン他の設定を記述。    
.pyと同階層にデータソースのファイル、Config.iniを配置してください。  
.pyと同階層にbotLog_yyyyMMdd.logが生成されます(拡張子、「botLog」部分はConfig.iniで変更可能)  
