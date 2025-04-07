/** @odoo-module **/

import { registry } from "@web/core/registry";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;

console.log("File loaded")
export class PosOrderSync extends Component {
    setup() {
        this.busService = useService("bus_service");
        this.pos = useService("pos");

        onMounted(() => {
            const tables = this.pos.tables;
            for (const table of tables) {
                const channel = `pos_order_sync_table_${table.id}`;
                this.busService.addChannel(channel);
            }

            this.busService.addEventListener("notification", this.onNotification);
        });
    }

    onNotification(notifications) {
        for (const notif of notifications) {
            const { payload, channel } = notif;
            if (payload.message === "new_order") {
                console.log("New order received:", payload);

                // You can refresh table screen or reload UI
                // Just reload the table screen (soft refresh)
                window.location.reload();
            }
        }
    }
}

registry.category("pos_screens").add("PosOrderSync", {
    Component: PosOrderSync,
});
