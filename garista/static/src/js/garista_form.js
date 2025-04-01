/** @odoo-module **/

import { useState, onWillStart } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";

console.log("✅ GaristaFormController JavaScript loaded successfully!");
export class GaristaFormController extends FormController {
    setup() {
        super.setup();
        this.state = useState({ showRestaurantField: false });

        onWillStart(() => {
            this.updateRestaurantVisibility();
        });

        this.model.root.on("update", () => {
            this.updateRestaurantVisibility();
        });
    }

    updateRestaurantVisibility() {
        const useExisting = this.model.root.data.use_existing_restaurant;
        this.state.showRestaurantField = !!useExisting;
    }
}

registry.category("views").add("garista_form_controller", {
    ...FormController,
    Controller: GaristaFormController,
});
