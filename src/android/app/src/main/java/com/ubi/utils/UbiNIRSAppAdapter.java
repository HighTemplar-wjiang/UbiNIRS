package com.ubi.utils;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import com.ubi.NanoScan.R;
import com.ubi.UbiNIRS.MainActivity;
import com.ubi.UbiNIRS.NewScanActivity;

import java.util.List;

public class UbiNIRSAppAdapter extends RecyclerView.Adapter<UbiNIRSAppAdapter.UbiNIRSAppViewHolder> {

    private List<UbiNIRSApp> ubiNIRSAppList;
    Context adapterContext;

    public UbiNIRSAppAdapter(List<UbiNIRSApp> ubiNIRSAppList, Context context) {
        this.ubiNIRSAppList = ubiNIRSAppList;
        this.adapterContext = context;
    }

    @Override
    public UbiNIRSAppViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View ubiNIRSView = LayoutInflater.from(parent.getContext()).inflate(
                R.layout.cardview_applist, parent, false);
        UbiNIRSAppViewHolder uvh = new UbiNIRSAppViewHolder(ubiNIRSView);
        return uvh;
    }

    @Override
    public void onBindViewHolder(UbiNIRSAppViewHolder holder, final int position) {
        holder.tvTitle.setText(ubiNIRSAppList.get(position).getAppName());
        holder.tvProvider.setText(ubiNIRSAppList.get(position).getAppProvider());
        holder.tvVersion.setText(ubiNIRSAppList.get(position).getAppVersion());
        holder.tvDescription.setText(ubiNIRSAppList.get(position).getAppDescription());
        // TODO: set up background image and icon.
    }

    @Override
    public int getItemCount() {
        return ubiNIRSAppList.size();
    }


    public class UbiNIRSAppViewHolder extends RecyclerView.ViewHolder{

        View mView;
        Context mContext;

        TextView tvTitle;
        TextView tvProvider;
        TextView tvVersion;
        TextView tvDescription;
        Switch swTrain;
        Button btnDelete;

        // TODO: Background image.

        public UbiNIRSAppViewHolder(final View view) {
            super(view);
            mView = view;
            mContext = view.getContext();


            mView.findViewById(R.id.cv_applist).setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View view) {
                    UbiNIRSApp ubiNIRSApp = ubiNIRSAppList.get(getAdapterPosition());

                    // Launch new scan activity.
                    Intent intent = new Intent(view.getContext(), NewScanActivity.class);
                    intent.putExtra("appMode", swTrain.isChecked());
                    intent.putExtra("appName", ubiNIRSApp.getAppName());
                    intent.putExtra("appServerAddress", ubiNIRSApp.getAppServerAddress());

                    view.getContext().startActivity(intent);
                }
            });

            // Find views.
            tvTitle = view.findViewById(R.id.tv_apptitle);
            tvProvider = view.findViewById(R.id.tv_provider);
            tvVersion = view.findViewById(R.id.tv_appversion);
            tvDescription = view.findViewById(R.id.tv_appdescription);
            swTrain = view.findViewById(R.id.sw_traintest);
            btnDelete = view.findViewById(R.id.btn_deleteapp);

            btnDelete.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View view) {
                    int position = getAdapterPosition();
                    final long appID = ubiNIRSAppList.get(position).getAppID();
                    String appName = ubiNIRSAppList.get(position).getAppName();

                    // Show a confirm dialog
                    new AlertDialog.Builder(mContext)
                            .setTitle("Delete NIRS App")
                            .setMessage("Do you want to remove " + appName + "?")
                            .setPositiveButton(android.R.string.yes, new DialogInterface.OnClickListener() {
                                @Override
                                public void onClick(DialogInterface dialogInterface, int i) {
                                    ((MainActivity) adapterContext).deleteNIRSApp(appID);
                                }
                            })
                            .setNegativeButton(android.R.string.no, null).show();

                    Toast.makeText(adapterContext, "Delete " + appName + "?", Toast.LENGTH_SHORT).show();
                }
            });
        }

    }
}
